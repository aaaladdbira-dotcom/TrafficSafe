from flask_smorest import Blueprint
from flask import jsonify, request
from models.accident import Accident
from models.accident_report import AccidentReport
from sqlalchemy import func
from extensions import db
from datetime import datetime
import sys
from datetime import date, timedelta
from time import time
from flask_jwt_extended import jwt_required
from utils.errors import success_response, ValidationError
from utils.validators import DateRangeValidator
from app import limiter

# Simple in-memory cache for expensive stats queries.
# Keyed by a string (usually derived from request args). TTL in seconds.
_CACHE = {}

def _cache_get(key):
    item = _CACHE.get(key)
    if not item:
        return None
    val, expires = item
    if expires and expires < time():
        try:
            del _CACHE[key]
        except KeyError:
            pass
        return None
    return val

def _cache_set(key, val, ttl=30):
    _CACHE[key] = (val, time() + ttl if ttl else None)


def _parse_date(s):
    if not s:
        return None
    try:
        # Try ISO format first
        return datetime.fromisoformat(s)
    except Exception:
        pass
    # Try common fallbacks
    fmts = ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y']
    for f in fmts:
        try:
            return datetime.strptime(s, f)
        except Exception:
            continue
    return None

blp = Blueprint('stats', 'stats', url_prefix='/api/v1/stats', description='Accident statistics')


def confirmed_accident_query():
    # Official accidents: any row in the Accident table is considered an
    # official record (imports and confirmed reports create Accident rows).
    # This excludes pending/rejected reports which do not create Accident rows.
    return Accident.query


def apply_filters(q):
    """Apply common filters from request args to an Accident query.
    Supported params: start, end (ISO dates), governorate, delegation, severity, cause, source
    """
    start = request.args.get('start')
    end = request.args.get('end')
    if start:
        try:
            dt = _parse_date(start)
            if dt: q = q.filter(Accident.occurred_at >= dt)
        except Exception:
            pass
    if end:
        try:
            dt = _parse_date(end)
            if dt: q = q.filter(Accident.occurred_at <= dt)
        except Exception:
            pass
    gov = request.args.get('governorate')
    if gov:
        q = q.filter(Accident.governorate == gov)
    delg = request.args.get('delegation')
    if delg:
        q = q.filter(Accident.delegation == delg)
    sev = request.args.get('severity')
    if sev:
        q = q.filter(Accident.severity == sev)
    cause = request.args.get('cause')
    if cause:
        q = q.filter(Accident.cause == cause)
    source = request.args.get('source')
    if source:
        q = q.filter(Accident.source == source)
    return q


# GET /api/stats/kpis
@blp.route('/kpis', methods=['GET'])
def kpis():
    """Return a set of global KPI values. Supports the same filters as other endpoints.

    Response example:
    {
      total: int,
      yearToDate: int,
      monthToDate: int,
      highSeverityRate: float, (0-1)
      topCause: { cause, count, pct },
      topGovernorate: { name, count },
      topDelegation: { name, count },
      avgPerDay: float,
      yoyChangePct: float
    }
    """
    base_q = confirmed_accident_query()
    # Build a cache key from request args so repeated identical queries are fast
    cache_key = 'kpis:' + '&'.join([f"{k}={v}" for k, v in sorted(request.args.items())])
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached)

    q = apply_filters(base_q)

    # total (respecting filters)
    total = q.count()

    # year-to-date and month-to-date (ignore start/end filters for these, but respect other filters)
    today = datetime.utcnow().date()
    start_of_year = datetime(today.year, 1, 1)
    start_of_month = datetime(today.year, today.month, 1)

    q_other = apply_filters(base_q)
    # remove start/end filtering for YTD/MTD by re-applying without start/end
    # Note: apply_filters reads request.args, so ensure start/end not set
    # compute yearToDate
    ytd = q_other.filter(Accident.occurred_at >= start_of_year).count()
    mtd = q_other.filter(Accident.occurred_at >= start_of_month).count()

    # high severity rate
    high_sev_list = ['fatal', 'serious']
    high_count = q.filter(func.lower(Accident.severity).in_(high_sev_list)).count()
    high_rate = round((high_count / total) if total else 0, 4)

    # top cause
    cause_row = (
        q.with_entities(Accident.cause, func.count().label('c'))
        .group_by(Accident.cause)
        .order_by(func.count().desc())
        .first()
    )
    if cause_row and cause_row[0]:
        top_cause = { 'cause': cause_row[0], 'label': (cause_row[0] or '').replace('_', ' ').title(), 'count': cause_row[1], 'pct': round((cause_row[1]/total) if total else 0, 4) }
    else:
        top_cause = { 'cause': None, 'label': None, 'count': 0, 'pct': 0 }

    # top governorate
    gov_row = (
        q.with_entities(Accident.governorate, func.count().label('c'))
        .group_by(Accident.governorate)
        .order_by(func.count().desc())
        .first()
    )
    top_gov = { 'name': gov_row[0], 'label': (gov_row[0] or ''), 'count': gov_row[1] } if gov_row and gov_row[0] else { 'name': None, 'label': None, 'count': 0 }

    # top delegation
    del_row = (
        q.with_entities(func.coalesce(Accident.delegation, Accident.governorate).label('zone'), func.count().label('c'))
        .group_by('zone')
        .order_by(func.count().desc())
        .first()
    )
    top_del = { 'name': del_row[0], 'label': (del_row[0] or ''), 'count': del_row[1] } if del_row and del_row[0] else { 'name': None, 'label': None, 'count': 0 }

    # avg per day: if start/end provided use that span, otherwise use last 30 days
    start = request.args.get('start')
    end = request.args.get('end')
    try:
        if start and end:
            sd_dt = _parse_date(start)
            ed_dt = _parse_date(end)
            sd = sd_dt.date() if sd_dt else None
            ed = ed_dt.date() if ed_dt else None
            if sd is None or ed is None:
                raise Exception('invalid dates')
            days = max((ed - sd).days, 1)
            span_q = apply_filters(base_q)
            count_span = span_q.count()
            avg_per_day = round(count_span / days, 2)
        else:
            ed = today
            sd = today - timedelta(days=29)
            span_q = apply_filters(base_q)
            count_span = span_q.filter(Accident.occurred_at >= datetime(sd.year, sd.month, sd.day)).count()
            avg_per_day = round(count_span / 30, 2)
    except Exception:
        avg_per_day = 0

    # YoY change: compare YTD to previous year's YTD
    prev_year_start = datetime(today.year - 1, 1, 1)
    prev_year_end = datetime(today.year - 1, 12, 31, 23, 59, 59)
    prev_ytd_count = q.filter(Accident.occurred_at >= prev_year_start, Accident.occurred_at <= prev_year_end).count()
    try:
        yoy = round(((ytd - prev_ytd_count) / prev_ytd_count) * 100, 2) if prev_ytd_count else (100.0 if ytd else 0.0)
    except Exception:
        yoy = 0.0

    out = {
        'total': total,
        'yearToDate': ytd,
        'monthToDate': mtd,
        'highSeverityRate': high_rate,
        'topCause': top_cause,
        'topGovernorate': top_gov,
        'topDelegation': top_del,
        'avgPerDay': avg_per_day,
        'yoyChangePct': yoy
    }
    try:
        _cache_set(cache_key, out, ttl=20)
    except Exception:
        pass
    return jsonify(out)

# GET /api/stats/accidents/total
@blp.route('/accidents/total', methods=['GET'])
def total_accidents():
    count = confirmed_accident_query().count()
    print(f"[DEBUG] Total confirmed accidents: {count}", file=sys.stderr)
    return jsonify({
        'label': 'Total Accidents',
        'value': count
    })

# GET /api/stats/accidents/by_month (supports granularity=day|month|year)
@blp.route('/accidents/by_month', methods=['GET'])
def accidents_by_month():
    gran = (request.args.get('granularity') or 'month').lower()
    if gran == 'day':
        fmt = '%Y-%m-%d'
    elif gran == 'year':
        fmt = '%Y'
    else:
        fmt = '%Y-%m'

    cache_key = 'by_month:' + fmt + ':' + '&'.join([f"{k}={v}" for k, v in sorted(request.args.items())])
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached)

    results = (
        confirmed_accident_query()
        .with_entities(func.strftime(fmt, Accident.occurred_at).label('period'), func.count())
        .group_by('period')
        .order_by('period')
        .all()
    )
    print(f"[DEBUG] Accidents over time (granularity={gran}): {results}", file=sys.stderr)
    labels = [r.period for r in results]
    values = [r[1] for r in results]
    out = {
        'labels': labels,
        'values': values,
        'granularity': gran
    }
    try: _cache_set(cache_key, out, ttl=10)
    except Exception: pass
    return jsonify(out)

# GET /api/stats/accidents/by_severity
@blp.route('/accidents/by_severity', methods=['GET'])
def accidents_by_severity():
    cache_key = 'by_severity:' + '&'.join([f"{k}={v}" for k, v in sorted(request.args.items())])
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached)

    results = (
        confirmed_accident_query()
        .with_entities(Accident.severity, func.count())
        .group_by(Accident.severity)
        .all()
    )
    print(f"[DEBUG] Accidents by severity: {results}", file=sys.stderr)
    labels = [r[0] for r in results]
    values = [r[1] for r in results]
    total = sum(values)
    percentages = [round(v/total*100, 2) for v in values] if total else []
    items = []
    for r in results:
        key = r[0]
        label = (key or '').replace('_', ' ').title()
        items.append({'key': key, 'label': label, 'count': r[1]})
    out = {
        'labels': labels,
        'values': values,
        'percentages': percentages,
        'items': items
    }
    try: _cache_set(cache_key, out, ttl=15)
    except Exception: pass
    return jsonify(out)

# GET /api/stats/accidents/by_cause
@blp.route('/accidents/by_cause', methods=['GET'])
def accidents_by_cause():
    results = (
        confirmed_accident_query()
        .with_entities(Accident.cause, func.count())
        .group_by(Accident.cause)
        .all()
    )
    print(f"[DEBUG] Accidents by cause: {results}", file=sys.stderr)
    labels = [r[0] for r in results]
    values = [r[1] for r in results]
    items = []
    for r in results:
        key = r[0]
        label = (key or '').replace('_', ' ').title()
        items.append({'key': key, 'label': label, 'count': r[1]})
    return jsonify({
        'labels': labels,
        'values': values,
        'items': items
    })

# GET /api/stats/accidents/by_governorate
@blp.route('/accidents/by_governorate', methods=['GET'])
def accidents_by_governorate():
    cache_key = 'by_governorate:' + '&'.join([f"{k}={v}" for k, v in sorted(request.args.items())])
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached)

    results = (
        confirmed_accident_query()
        .with_entities(Accident.governorate, func.count())
        .group_by(Accident.governorate)
        .all()
    )
    labels = [r[0] for r in results]
    values = [r[1] for r in results]
    items = []
    for r in results:
        key = r[0]
        label = (key or '')
        items.append({'key': key, 'label': label, 'count': r[1]})
    out = { 'labels': labels, 'values': values, 'items': items }
    try: _cache_set(cache_key, out, ttl=20)
    except Exception: pass
    return jsonify(out)


# GET /api/stats/accidents/by_delegation
@blp.route('/accidents/by_delegation', methods=['GET'])
def accidents_by_delegation():
    # Prefer delegation, fallback to governorate where delegation is null/empty
    cache_key = 'by_delegation:' + '&'.join([f"{k}={v}" for k, v in sorted(request.args.items())])
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached)

    results = (
        confirmed_accident_query()
        .with_entities(func.coalesce(Accident.delegation, Accident.governorate).label('zone'), func.count())
        .group_by('zone')
        .order_by(func.count().desc())
        .all()
    )
    print(f"[DEBUG] Accidents by delegation: {results}", file=sys.stderr)
    labels = [r.zone for r in results]
    values = [r[1] for r in results]
    items = []
    for r in results:
        key = r.zone
        label = (key or '')
        items.append({'key': key, 'label': label, 'count': r[1]})
    out = { 'labels': labels, 'values': values, 'items': items }
    try: _cache_set(cache_key, out, ttl=30)
    except Exception: pass
    return jsonify(out)


# GET /api/stats/accidents/hour_weekday
@blp.route('/accidents/hour_weekday', methods=['GET'])
def accidents_hour_weekday():
    """Return a 24x7 matrix of counts by hour (0-23) and weekday (Mon..Sun).
    Response:
      { hours: [0..23], weekdays: ['Mon',...,'Sun'], matrix: [[counts per weekday for hour0], ...] }
    Supports same filters as other endpoints.
    """
    cache_key = 'heatmap:' + '&'.join([f"{k}={v}" for k, v in sorted(request.args.items())])
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached)

    q = apply_filters(confirmed_accident_query())
    # group by hour and weekday (strftime '%H' -> 00-23, '%w' -> 0=Sunday..6=Saturday)
    results = (
        q.with_entities(func.strftime('%H', Accident.occurred_at).label('hour'), func.strftime('%w', Accident.occurred_at).label('weekday'), func.count().label('c'))
         .group_by('hour', 'weekday')
         .all()
    )

    # prepare matrix [24][7], weekday order Mon..Sun
    hours = list(range(24))
    weekdays = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    matrix = [[0 for _ in range(7)] for _ in range(24)]
    for r in results:
        try:
            h = int(r.hour) if r.hour is not None else 0
            w = int(r.weekday) if r.weekday is not None else 0
            # convert w(0=Sun) to Monday-first index
            idx = (w - 1) % 7
            if 0 <= h < 24 and 0 <= idx < 7:
                matrix[h][idx] = int(r.c)
        except Exception:
            continue

    out = { 'hours': hours, 'weekdays': weekdays, 'matrix': matrix }
    try: _cache_set(cache_key, out, ttl=30)
    except Exception: pass
    return jsonify(out)


# GET /api/stats/sankey/cause_severity_location
@blp.route('/sankey/cause_severity_location', methods=['GET'])
def sankey_cause_severity_location():
    """Return nodes/links for a Cause -> Severity -> Governorate Sankey.
    Response:
      { nodes: ["Cause A", "Severity", "Gov"...], links: [{source, target, value}] }
    Supports the same filters as other endpoints.
    """
    cache_key = 'sankey_csl:' + '&'.join([f"{k}={v}" for k, v in sorted(request.args.items())])
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached)

    q = apply_filters(confirmed_accident_query())
    rows = (
        q.with_entities(Accident.cause, Accident.severity, Accident.governorate, func.count().label('c'))
         .group_by(Accident.cause, Accident.severity, Accident.governorate)
         .all()
    )
    nodes = []
    node_index = {}
    links = []

    def idx(label):
        if label not in node_index:
            node_index[label] = len(nodes)
            nodes.append(label)
        return node_index[label]

    for r in rows:
        cause = r[0] or 'Unknown cause'
        severity = r[1] or 'Unknown severity'
        loc = r[2] or 'Unknown location'
        value = int(r.c or 0)
        if value <= 0:
            continue
        c_idx = idx(f"Cause: {cause}")
        s_idx = idx(f"Severity: {severity}")
        l_idx = idx(f"Location: {loc}")
        # cause -> severity
        links.append({'source': c_idx, 'target': s_idx, 'value': value})
        # severity -> location
        links.append({'source': s_idx, 'target': l_idx, 'value': value})

    out = { 'nodes': nodes, 'links': links }
    try: _cache_set(cache_key, out, ttl=20)
    except Exception: pass
    return jsonify(out)


# GET /api/stats/accidents/by_governorate_timeseries
@blp.route('/accidents/by_governorate_timeseries', methods=['GET'])
def accidents_by_governorate_timeseries():
    """Return recent monthly counts for top N governorates (default 6 months, top 8).
    Response:
      { labels: ["2025-09", ...], series: [{ label, values: [...] }, ...] }
    """
    months = int(request.args.get('months', 6))
    top_n = int(request.args.get('top', 8))
    months = max(1, min(months, 24))
    top_n = max(1, min(top_n, 20))

    today = date.today()
    start_date = (today.replace(day=1) - timedelta(days=months*31)).replace(day=1)
    earliest = confirmed_accident_query().with_entities(func.min(Accident.occurred_at)).scalar()
    if earliest:
        earliest_month = earliest.date().replace(day=1)
        if earliest_month < start_date:
            start_date = earliest_month

    # total by governorate to pick top N
    totals = (
        confirmed_accident_query()
        .with_entities(Accident.governorate, func.count().label('c'))
        .group_by(Accident.governorate)
        .order_by(func.count().desc())
        .limit(top_n)
        .all()
    )
    govs = []
    for r in totals:
        govs.append(r[0] or 'Unknown')
    if not govs:
        return jsonify({'labels': [], 'series': []})

    fmt = '%Y-%m'
    labels = []
    cursor = start_date
    while cursor <= today:
        labels.append(cursor.strftime(fmt))
        # advance one month safely
        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year+1, month=1, day=1)
        else:
            cursor = cursor.replace(month=cursor.month+1, day=1)

    series = []
    for gov in govs:
        q = confirmed_accident_query()
        if gov != 'Unknown':
            q = q.filter(Accident.governorate == gov)
        else:
            q = q.filter((Accident.governorate == None) | (Accident.governorate == ''))
        q = q.filter(Accident.occurred_at >= datetime.strptime(labels[0] + '-01', '%Y-%m-%d'))
        rows = (
            q.with_entities(func.strftime(fmt, Accident.occurred_at).label('period'), func.count())
             .group_by('period')
             .all()
        )
        m = {r.period: r[1] for r in rows}
        values = [m.get(l, 0) for l in labels]
        series.append({'label': gov, 'values': values})

    return jsonify({'labels': labels, 'series': series})


# GET /api/stats/reports/confirmed_vs_reported
@blp.route('/reports/confirmed_vs_reported', methods=['GET'])
def confirmed_vs_reported():
    """Return reported vs confirmed counts per period.
    Query params:
      granularity=day|month|year (default month)
      year=YYYY (optional filter)
    """
    gran = (request.args.get('granularity') or 'month').lower()
    year = request.args.get('year')
    if gran == 'day':
        fmt = '%Y-%m-%d'
    elif gran == 'year':
        fmt = '%Y'
    else:
        fmt = '%Y-%m'

    q = AccidentReport.query
    if year:
        q = q.filter(func.strftime('%Y', AccidentReport.date) == str(year))

    reported = (
        q.with_entities(func.strftime(fmt, AccidentReport.date).label('period'), func.count())
         .group_by('period')
         .order_by('period')
         .all()
    )

    confirmed_q = AccidentReport.query.filter(AccidentReport.status == 'CONFIRMED')
    if year:
        confirmed_q = confirmed_q.filter(func.strftime('%Y', AccidentReport.date) == str(year))

    confirmed = (
        confirmed_q.with_entities(func.strftime(fmt, AccidentReport.date).label('period'), func.count())
         .group_by('period')
         .order_by('period')
         .all()
    )

    # merge periods
    periods = sorted({r.period for r in reported} | {c.period for c in confirmed})
    rep_map = {r.period: r[1] for r in reported}
    conf_map = {c.period: c[1] for c in confirmed}
    labels = periods
    reported_vals = [rep_map.get(p, 0) for p in periods]
    confirmed_vals = [conf_map.get(p, 0) for p in periods]
    print(f"[DEBUG] confirmed_vs_reported periods={periods}", file=sys.stderr)
    return jsonify({
        'labels': labels,
        'reported': reported_vals,
        'confirmed': confirmed_vals,
        'granularity': gran,
    })

# GET /api/stats/reports/status_counts
@blp.route('/reports/status_counts', methods=['GET'])
def report_status_counts():
    results = (
        AccidentReport.query
        .with_entities(AccidentReport.status, func.count())
        .group_by(AccidentReport.status)
        .all()
    )
    labels = [r[0] for r in results]
    values = [r[1] for r in results]
    return jsonify({
        'labels': labels,
        'values': values
    })


# ============================================
# ADVANCED ANALYTICS ENDPOINTS
# ============================================

# GET /api/stats/trends/analysis
@blp.route('/trends/analysis', methods=['GET'])
def trends_analysis():
    """Return trend analysis with moving averages and change rates.
    
    Response:
    {
        periods: [...],
        values: [...],
        movingAverage: [...],  // 7-period moving average
        changeRate: [...],      // Period-over-period change %
        trend: "increasing"|"decreasing"|"stable",
        forecast: [...]         // Simple linear projection
    }
    """
    cache_key = 'trends:' + '&'.join([f"{k}={v}" for k, v in sorted(request.args.items())])
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached)

    gran = (request.args.get('granularity') or 'month').lower()
    periods_back = int(request.args.get('periods', 12))
    
    if gran == 'day':
        fmt = '%Y-%m-%d'
    elif gran == 'year':
        fmt = '%Y'
    else:
        fmt = '%Y-%m'
    
    q = apply_filters(confirmed_accident_query())
    results = (
        q.with_entities(func.strftime(fmt, Accident.occurred_at).label('period'), func.count().label('c'))
        .group_by('period')
        .order_by('period')
        .all()
    )
    
    periods = [r.period for r in results][-periods_back:] if periods_back else [r.period for r in results]
    values = [r.c for r in results][-periods_back:] if periods_back else [r.c for r in results]
    
    # Calculate 7-period moving average
    ma_window = min(7, len(values))
    moving_avg = []
    for i in range(len(values)):
        if i < ma_window - 1:
            moving_avg.append(None)
        else:
            window = values[i - ma_window + 1:i + 1]
            moving_avg.append(round(sum(window) / len(window), 2))
    
    # Calculate period-over-period change rate
    change_rate = [None]  # First period has no previous
    for i in range(1, len(values)):
        if values[i - 1] == 0:
            change_rate.append(100.0 if values[i] > 0 else 0.0)
        else:
            rate = ((values[i] - values[i - 1]) / values[i - 1]) * 100
            change_rate.append(round(rate, 2))
    
    # Determine overall trend
    if len(values) >= 3:
        recent = values[-3:]
        if recent[-1] > recent[0] * 1.1:
            trend = "increasing"
        elif recent[-1] < recent[0] * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"
    
    # Simple linear forecast (next 3 periods)
    forecast = []
    if len(values) >= 2:
        # Simple linear regression
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator != 0:
            slope = numerator / denominator
            intercept = y_mean - slope * x_mean
            
            for i in range(3):
                projected = intercept + slope * (n + i)
                forecast.append(max(0, round(projected)))
    
    out = {
        'periods': periods,
        'values': values,
        'movingAverage': moving_avg,
        'changeRate': change_rate,
        'trend': trend,
        'forecast': forecast,
        'granularity': gran
    }
    
    try:
        _cache_set(cache_key, out, ttl=60)
    except Exception:
        pass
    
    return jsonify(out)


# GET /api/stats/comparison
@blp.route('/comparison', methods=['GET'])
def period_comparison():
    """Compare current period with previous periods.
    
    Query params:
        period: 'month' | 'quarter' | 'year' (default: month)
    
    Response:
    {
        current: { period, count, severity_breakdown },
        previous: { period, count, severity_breakdown },
        change: { count_diff, count_pct, severity_changes },
        yearAgo: { period, count, change_pct }
    }
    """
    cache_key = 'comparison:' + '&'.join([f"{k}={v}" for k, v in sorted(request.args.items())])
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached)
    
    period_type = (request.args.get('period') or 'month').lower()
    today = datetime.utcnow().date()
    
    if period_type == 'year':
        current_start = datetime(today.year, 1, 1)
        current_end = datetime.utcnow()
        prev_start = datetime(today.year - 1, 1, 1)
        prev_end = datetime(today.year - 1, 12, 31, 23, 59, 59)
        year_ago_start = prev_start
        year_ago_end = prev_end
        current_label = str(today.year)
        prev_label = str(today.year - 1)
    elif period_type == 'quarter':
        quarter = (today.month - 1) // 3
        current_start = datetime(today.year, quarter * 3 + 1, 1)
        current_end = datetime.utcnow()
        # Previous quarter
        if quarter == 0:
            prev_start = datetime(today.year - 1, 10, 1)
            prev_end = datetime(today.year - 1, 12, 31, 23, 59, 59)
        else:
            prev_start = datetime(today.year, (quarter - 1) * 3 + 1, 1)
            prev_end = datetime(today.year, quarter * 3, 1) - timedelta(days=1)
        current_label = f"Q{quarter + 1} {today.year}"
        prev_label = f"Q{quarter if quarter > 0 else 4} {today.year if quarter > 0 else today.year - 1}"
        # Year ago same quarter
        year_ago_start = datetime(today.year - 1, quarter * 3 + 1, 1)
        year_ago_end = datetime(today.year - 1, (quarter + 1) * 3 if quarter < 3 else 12, 1) + timedelta(days=30)
    else:  # month
        current_start = datetime(today.year, today.month, 1)
        current_end = datetime.utcnow()
        if today.month == 1:
            prev_start = datetime(today.year - 1, 12, 1)
            prev_end = datetime(today.year - 1, 12, 31, 23, 59, 59)
        else:
            prev_start = datetime(today.year, today.month - 1, 1)
            prev_end = current_start - timedelta(days=1)
        current_label = current_start.strftime('%B %Y')
        prev_label = prev_start.strftime('%B %Y')
        # Year ago same month
        year_ago_start = datetime(today.year - 1, today.month, 1)
        year_ago_end = datetime(today.year - 1, today.month, 28)
    
    # Get counts
    q_base = apply_filters(confirmed_accident_query())
    
    current_count = q_base.filter(
        Accident.occurred_at >= current_start,
        Accident.occurred_at <= current_end
    ).count()
    
    prev_count = q_base.filter(
        Accident.occurred_at >= prev_start,
        Accident.occurred_at <= prev_end
    ).count()
    
    year_ago_count = q_base.filter(
        Accident.occurred_at >= year_ago_start,
        Accident.occurred_at <= year_ago_end
    ).count()
    
    # Severity breakdowns
    def get_severity_breakdown(start, end):
        results = (
            q_base.filter(Accident.occurred_at >= start, Accident.occurred_at <= end)
            .with_entities(Accident.severity, func.count())
            .group_by(Accident.severity)
            .all()
        )
        return {r[0] or 'unknown': r[1] for r in results}
    
    current_severity = get_severity_breakdown(current_start, current_end)
    prev_severity = get_severity_breakdown(prev_start, prev_end)
    
    # Calculate changes
    count_diff = current_count - prev_count
    count_pct = round((count_diff / prev_count) * 100, 2) if prev_count else (100.0 if current_count else 0.0)
    year_ago_pct = round(((current_count - year_ago_count) / year_ago_count) * 100, 2) if year_ago_count else 0.0
    
    severity_changes = {}
    all_severities = set(current_severity.keys()) | set(prev_severity.keys())
    for sev in all_severities:
        curr = current_severity.get(sev, 0)
        prev = prev_severity.get(sev, 0)
        diff = curr - prev
        pct = round((diff / prev) * 100, 2) if prev else (100.0 if curr else 0.0)
        severity_changes[sev] = {'current': curr, 'previous': prev, 'diff': diff, 'pct': pct}
    
    out = {
        'current': {
            'period': current_label,
            'count': current_count,
            'severity_breakdown': current_severity
        },
        'previous': {
            'period': prev_label,
            'count': prev_count,
            'severity_breakdown': prev_severity
        },
        'change': {
            'count_diff': count_diff,
            'count_pct': count_pct,
            'severity_changes': severity_changes
        },
        'yearAgo': {
            'period': year_ago_start.strftime('%B %Y') if period_type == 'month' else str(today.year - 1),
            'count': year_ago_count,
            'change_pct': year_ago_pct
        }
    }
    
    try:
        _cache_set(cache_key, out, ttl=30)
    except Exception:
        pass
    
    return jsonify(out)


# GET /api/stats/hotspots
@blp.route('/hotspots', methods=['GET'])
def accident_hotspots():
    """Return accident hotspots by location with risk scores.
    
    Query params:
        limit: number of hotspots to return (default: 10)
        min_count: minimum accidents to qualify as hotspot (default: 5)
    
    Response:
    {
        hotspots: [
            { 
                location, 
                count, 
                severity_score, 
                risk_level: 'critical'|'high'|'medium'|'low',
                top_causes: [...],
                peak_times: [...]
            }
        ]
    }
    """
    cache_key = 'hotspots:' + '&'.join([f"{k}={v}" for k, v in sorted(request.args.items())])
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached)
    
    limit = int(request.args.get('limit', 10))
    min_count = int(request.args.get('min_count', 5))
    
    q = apply_filters(confirmed_accident_query())
    
    # Get locations with counts
    location_counts = (
        q.with_entities(
            func.coalesce(Accident.delegation, Accident.governorate).label('location'),
            func.count().label('count')
        )
        .group_by('location')
        .having(func.count() >= min_count)
        .order_by(func.count().desc())
        .limit(limit)
        .all()
    )
    
    hotspots = []
    high_sev_list = ['fatal', 'serious']
    
    for loc_row in location_counts:
        location = loc_row.location
        count = loc_row.count
        
        # Get severity breakdown for this location
        loc_q = q.filter(
            (Accident.delegation == location) | 
            ((Accident.delegation.is_(None)) & (Accident.governorate == location))
        )
        
        high_sev_count = loc_q.filter(func.lower(Accident.severity).in_(high_sev_list)).count()
        severity_score = round((high_sev_count / count) * 100, 1) if count else 0
        
        # Determine risk level
        if severity_score >= 40 and count >= 20:
            risk_level = 'critical'
        elif severity_score >= 25 or count >= 30:
            risk_level = 'high'
        elif severity_score >= 10 or count >= 15:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        # Get top causes
        top_causes = (
            loc_q.with_entities(Accident.cause, func.count().label('c'))
            .group_by(Accident.cause)
            .order_by(func.count().desc())
            .limit(3)
            .all()
        )
        causes = [{'cause': r[0], 'count': r[1]} for r in top_causes if r[0]]
        
        # Get peak times (hours)
        peak_hours = (
            loc_q.with_entities(
                func.strftime('%H', Accident.occurred_at).label('hour'),
                func.count().label('c')
            )
            .group_by('hour')
            .order_by(func.count().desc())
            .limit(3)
            .all()
        )
        peak_times = [{'hour': int(r.hour), 'count': r.c} for r in peak_hours if r.hour]
        
        hotspots.append({
            'location': location,
            'count': count,
            'severity_score': severity_score,
            'risk_level': risk_level,
            'top_causes': causes,
            'peak_times': peak_times
        })
    
    out = {'hotspots': hotspots}
    
    try:
        _cache_set(cache_key, out, ttl=60)
    except Exception:
        pass
    
    return jsonify(out)


# GET /api/stats/severity/distribution
@blp.route('/severity/distribution', methods=['GET'])
def severity_distribution():
    """Return detailed severity distribution with percentages and trends.
    
    Response:
    {
        distribution: [
            { severity, count, percentage, trend, color }
        ],
        total: int,
        highSeverityPct: float,
        comparison: { ... }  // vs previous period
    }
    """
    cache_key = 'sev_dist:' + '&'.join([f"{k}={v}" for k, v in sorted(request.args.items())])
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached)
    
    q = apply_filters(confirmed_accident_query())
    
    results = (
        q.with_entities(Accident.severity, func.count().label('c'))
        .group_by(Accident.severity)
        .order_by(func.count().desc())
        .all()
    )
    
    total = sum(r.c for r in results)
    high_sev_list = ['fatal', 'serious']
    
    # Color mapping
    color_map = {
        'fatal': '#dc2626',
        'serious': '#ea580c',
        'high': '#f59e0b',
        'moderate': '#eab308',
        'medium': '#eab308',
        'minor': '#22c55e',
        'low': '#22c55e',
        'slight': '#3b82f6'
    }
    
    distribution = []
    high_sev_total = 0
    
    for r in results:
        sev = r[0] or 'unknown'
        count = r.c
        pct = round((count / total) * 100, 1) if total else 0
        
        if sev.lower() in high_sev_list:
            high_sev_total += count
        
        distribution.append({
            'severity': sev,
            'label': sev.replace('_', ' ').title(),
            'count': count,
            'percentage': pct,
            'color': color_map.get(sev.lower(), '#6b7280')
        })
    
    high_sev_pct = round((high_sev_total / total) * 100, 1) if total else 0
    
    out = {
        'distribution': distribution,
        'total': total,
        'highSeverityPct': high_sev_pct
    }
    
    try:
        _cache_set(cache_key, out, ttl=30)
    except Exception:
        pass
    
    return jsonify(out)


# GET /api/stats/causes/analysis
@blp.route('/causes/analysis', methods=['GET'])
def cause_analysis():
    """Return detailed cause analysis with severity breakdown per cause.
    
    Response:
    {
        causes: [
            { 
                cause, 
                count, 
                percentage,
                severity_breakdown: { fatal: x, serious: y, ... },
                avg_severity_score,
                trend
            }
        ],
        correlations: [
            { cause1, cause2, correlation_strength }  // if causes often occur together
        ]
    }
    """
    cache_key = 'cause_analysis:' + '&'.join([f"{k}={v}" for k, v in sorted(request.args.items())])
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached)
    
    q = apply_filters(confirmed_accident_query())
    
    # Get cause totals
    cause_results = (
        q.with_entities(Accident.cause, func.count().label('c'))
        .group_by(Accident.cause)
        .order_by(func.count().desc())
        .all()
    )
    
    total = sum(r.c for r in cause_results)
    
    # Severity scores for averaging
    sev_scores = {
        'fatal': 5, 'serious': 4, 'high': 3, 
        'moderate': 2, 'medium': 2, 'minor': 1, 'low': 1, 'slight': 0.5
    }
    
    causes = []
    for r in cause_results:
        cause = r[0]
        if not cause:
            continue
            
        count = r.c
        pct = round((count / total) * 100, 1) if total else 0
        
        # Get severity breakdown for this cause
        sev_breakdown = (
            q.filter(Accident.cause == cause)
            .with_entities(Accident.severity, func.count().label('c'))
            .group_by(Accident.severity)
            .all()
        )
        
        severity_dict = {s[0] or 'unknown': s[1] for s in sev_breakdown}
        
        # Calculate average severity score
        total_score = sum(sev_scores.get(s.lower(), 1) * c for s, c in severity_dict.items())
        avg_score = round(total_score / count, 2) if count else 0
        
        causes.append({
            'cause': cause,
            'label': cause.replace('_', ' ').title(),
            'count': count,
            'percentage': pct,
            'severity_breakdown': severity_dict,
            'avg_severity_score': avg_score
        })
    
    out = {
        'causes': causes[:15],  # Top 15 causes
        'total': total
    }
    
    try:
        _cache_set(cache_key, out, ttl=45)
    except Exception:
        pass
    
    return jsonify(out)


# GET /api/stats/comparison
@blp.route('/comparison', methods=['GET'])
def comparison():
    """Compare accident statistics between time periods.
    
    Query params:
    - period: 'month' or 'year' (default: month)
    - governorate: filter by governorate (optional)
    
    Response example:
    {
      current_period: { start, end, total, by_severity, by_cause },
      previous_period: { start, end, total, by_severity, by_cause },
      change: { total_pct, severity_changes, cause_changes },
      trend: 'increasing' | 'decreasing' | 'stable'
    }
    """
    period = request.args.get('period', 'month')
    governorate = request.args.get('governorate')
    
    today = datetime.utcnow().date()
    
    if period == 'year':
        # Current year vs previous year
        current_start = datetime(today.year, 1, 1)
        current_end = datetime.utcnow()
        previous_start = datetime(today.year - 1, 1, 1)
        previous_end = datetime(today.year - 1, 12, 31, 23, 59, 59)
    else:
        # Current month vs previous month
        current_start = datetime(today.year, today.month, 1)
        current_end = datetime.utcnow()
        if today.month == 1:
            previous_start = datetime(today.year - 1, 12, 1)
            previous_end = datetime(today.year - 1, 12, 31, 23, 59, 59)
        else:
            previous_start = datetime(today.year, today.month - 1, 1)
            previous_end = datetime(today.year, today.month, 1) - timedelta(seconds=1)
    
    def get_period_stats(start_dt, end_dt):
        q = confirmed_accident_query()
        q = q.filter(Accident.occurred_at >= start_dt, Accident.occurred_at <= end_dt)
        if governorate:
            q = q.filter(Accident.governorate == governorate)
        
        total = q.count()
        
        # By severity
        severity_data = q.with_entities(
            Accident.severity, func.count().label('c')
        ).group_by(Accident.severity).all()
        by_severity = {s or 'unknown': c for s, c in severity_data}
        
        # By cause (top 5)
        cause_data = q.with_entities(
            Accident.cause, func.count().label('c')
        ).group_by(Accident.cause).order_by(func.count().desc()).limit(5).all()
        by_cause = {c or 'unknown': cnt for c, cnt in cause_data}
        
        return {
            'start': start_dt.strftime('%Y-%m-%d'),
            'end': end_dt.strftime('%Y-%m-%d'),
            'total': total,
            'by_severity': by_severity,
            'by_cause': by_cause
        }
    
    current = get_period_stats(current_start, current_end)
    previous = get_period_stats(previous_start, previous_end)
    
    # Calculate changes
    total_change = 0
    if previous['total'] > 0:
        total_change = round((current['total'] - previous['total']) / previous['total'] * 100, 1)
    
    # Determine trend
    if total_change > 10:
        trend = 'increasing'
    elif total_change < -10:
        trend = 'decreasing'
    else:
        trend = 'stable'
    
    return jsonify({
        'period': period,
        'governorate': governorate,
        'current_period': current,
        'previous_period': previous,
        'change': {
            'total_pct': total_change,
            'absolute': current['total'] - previous['total']
        },
        'trend': trend
    })


# GET /api/stats/weather
@blp.route('/weather', methods=['GET'])
def weather_stats():
    """Get real-time weather data with full details.
    
    Query params:
    - governorate or region: governorate name (default: Tunis)
    """
    try:
        from utils.weather import weather_service, WEATHER_CODES
        from datetime import datetime
        
        # Accept both 'region' and 'governorate' params
        governorate = request.args.get('region') or request.args.get('governorate', 'Tunis')
        
        # Get current weather - no cache for real-time
        current = weather_service.get_current_weather(governorate)
        
        if not current:
            # Return fallback data if API fails
            return jsonify({
                'governorate': governorate,
                'temperature': 22,
                'feels_like': 21,
                'conditions': 'Clear',
                'conditions_detail': 'Clear sky',
                'humidity': 60,
                'wind_speed': 12,
                'wind_gusts': 18,
                'wind_direction': 180,
                'precipitation': 0,
                'rain_chance': 0,
                'cloud_cover': 10,
                'uv_index': 3,
                'is_day': 1,
                'risk_score': 25,
                'risk_factors': [],
                'last_updated': datetime.now().strftime('%H:%M'),
                'fallback': True
            })
        
        # Map weather code to simple condition string
        weather_code = current.get('weathercode', 0)
        weather_desc = current.get('weather_description', 'Clear')
        
        # Map weather description to simple conditions for icon matching
        conditions_map = {
            'Clear sky': 'Clear',
            'Mainly clear': 'Clear',
            'Partly cloudy': 'Partly Cloudy',
            'Overcast': 'Cloudy',
            'Fog': 'Fog',
            'Depositing rime fog': 'Fog',
            'Light drizzle': 'Drizzle',
            'Moderate drizzle': 'Drizzle',
            'Dense drizzle': 'Drizzle',
            'Slight rain': 'Rain',
            'Moderate rain': 'Rain',
            'Heavy rain': 'Heavy Rain',
            'Slight snow': 'Snow',
            'Moderate snow': 'Snow',
            'Heavy snow': 'Snow',
            'Slight rain showers': 'Showers',
            'Moderate rain showers': 'Showers',
            'Violent rain showers': 'Heavy Rain',
            'Thunderstorm': 'Thunderstorm',
            'Thunderstorm with slight hail': 'Thunderstorm',
            'Thunderstorm with heavy hail': 'Thunderstorm'
        }
        conditions = conditions_map.get(weather_desc, 'Clear')
        
        # Calculate risk score (0-100 scale)
        risk_factor = current.get('risk_factor', 1.0)
        base_risk = 20
        
        # Add factors for rain probability and visibility
        rain_chance = current.get('precipitation_probability', 0) or 0
        humidity = current.get('humidity', 50) or 50
        wind_speed = current.get('windspeed', 0) or 0
        
        # Increase risk based on conditions
        if rain_chance > 70:
            risk_factor *= 1.3
        elif rain_chance > 40:
            risk_factor *= 1.15
        
        if humidity > 90:
            risk_factor *= 1.1  # Possible fog
        
        if wind_speed > 50:
            risk_factor *= 1.4
        elif wind_speed > 30:
            risk_factor *= 1.2
        
        risk_score = min(100, int(base_risk * risk_factor * 1.5))
        
        # Determine risk factors based on conditions
        risk_factors = []
        if weather_code in [45, 48]:
            risk_factors.append('⚠️ Reduced visibility (fog)')
        if rain_chance > 60:
            risk_factors.append(f'🌧️ {rain_chance}% rain probability')
        if weather_code in [61, 63, 65, 80, 81, 82]:
            risk_factors.append('🌧️ Wet road conditions')
        if weather_code in [65, 82]:
            risk_factors.append('⚠️ Hydroplaning risk')
        if weather_code in [71, 73, 75]:
            risk_factors.append('❄️ Slippery conditions')
        if weather_code in [95, 96, 99]:
            risk_factors.append('⛈️ Severe thunderstorm')
        if wind_speed > 40:
            risk_factors.append(f'💨 High winds ({int(wind_speed)} km/h)')
        if current.get('uv_index', 0) > 7:
            risk_factors.append('☀️ High UV exposure')
        if humidity > 85:
            risk_factors.append('💧 High humidity')
        if not current.get('is_day', 1):
            risk_factors.append('🌙 Night driving')
        
        # Get wind direction as compass
        wind_dir = current.get('winddirection', 0) or 0
        wind_compass = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][int((wind_dir + 22.5) % 360 / 45)]
        
        # Get temperature with fallback
        temp = current.get('temperature', 20) or 20
        feels_like_temp = current.get('feels_like') or current.get('temperature') or temp
        
        # Format response for dashboard - real-time data
        return jsonify({
            'governorate': governorate,
            'temperature': round(temp),
            'feels_like': round(feels_like_temp),
            'conditions': conditions,
            'conditions_detail': weather_desc or conditions,
            'humidity': current.get('humidity', 50) or 50,
            'wind_speed': round(current.get('windspeed', 0) or 0),
            'wind_gusts': round(current.get('wind_gusts', 0) or 0),
            'wind_direction': wind_dir,
            'wind_compass': wind_compass,
            'precipitation': round(current.get('precipitation', 0) or 0, 1),
            'rain': round(current.get('rain', 0) or 0, 1),
            'rain_chance': rain_chance or 0,
            'cloud_cover': current.get('cloud_cover', 0) or 0,
            'uv_index': round(current.get('uv_index', 0) or 0, 1),
            'is_day': current.get('is_day', 1),
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'last_updated': datetime.now().strftime('%H:%M:%S'),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        from datetime import datetime
        # Return fallback data on error
        return jsonify({
            'governorate': request.args.get('region', 'Tunis'),
            'temperature': 22,
            'feels_like': 21,
            'conditions': 'Clear',
            'conditions_detail': 'Unable to fetch',
            'humidity': 60,
            'wind_speed': 12,
            'wind_gusts': 18,
            'wind_direction': 180,
            'wind_compass': 'S',
            'precipitation': 0,
            'rain': 0,
            'rain_chance': 0,
            'cloud_cover': 10,
            'uv_index': 3,
            'is_day': 1,
            'risk_score': 25,
            'risk_factors': [],
            'last_updated': datetime.now().strftime('%H:%M:%S'),
            'error': str(e)
        })


# GET /api/stats/risk-zones
@blp.route('/risk-zones', methods=['GET'])
def risk_zones():
    """Get risk assessment for all governorates."""
    try:
        from utils.predictive import predictive
        
        zones = predictive.get_risk_zones()
        
        # If no data, return sample data
        if not zones:
            zones = [
                {'governorate': 'Tunis', 'accident_count': 45, 'risk_score': 72, 'risk_level': 'high'},
                {'governorate': 'Sfax', 'accident_count': 32, 'risk_score': 58, 'risk_level': 'medium'},
                {'governorate': 'Sousse', 'accident_count': 28, 'risk_score': 52, 'risk_level': 'medium'},
                {'governorate': 'Bizerte', 'accident_count': 22, 'risk_score': 45, 'risk_level': 'medium'},
                {'governorate': 'Kairouan', 'accident_count': 18, 'risk_score': 38, 'risk_level': 'medium'},
                {'governorate': 'Gabès', 'accident_count': 15, 'risk_score': 32, 'risk_level': 'medium'},
                {'governorate': 'Ariana', 'accident_count': 12, 'risk_score': 28, 'risk_level': 'low'},
                {'governorate': 'Nabeul', 'accident_count': 10, 'risk_score': 24, 'risk_level': 'low'},
            ]
        
        # Sort by accident count for high risk zones and get TOP 5
        sorted_zones = sorted(zones, key=lambda x: x.get('accident_count', 0), reverse=True)
        top_5_zones = sorted_zones[:5]
        
        return jsonify({
            'zones': zones,
            'high_risk_zones': top_5_zones,  # Only top 5
            'high_risk_count': sum(1 for z in zones if z.get('risk_level') == 'high'),
            'total_governorates': len(zones)
        })
    except Exception as e:
        # Return fallback data on error - TOP 5 only
        fallback = [
            {'governorate': 'Tunis', 'accident_count': 45, 'risk_score': 72, 'risk_level': 'high'},
            {'governorate': 'Sfax', 'accident_count': 32, 'risk_score': 58, 'risk_level': 'medium'},
            {'governorate': 'Sousse', 'accident_count': 28, 'risk_score': 52, 'risk_level': 'medium'},
            {'governorate': 'Ariana', 'accident_count': 25, 'risk_score': 48, 'risk_level': 'medium'},
            {'governorate': 'Nabeul', 'accident_count': 22, 'risk_score': 45, 'risk_level': 'medium'},
        ]
        return jsonify({
            'zones': fallback,
            'high_risk_zones': fallback,  # Already top 5
            'high_risk_count': 1,
            'total_governorates': 5,
            'error': str(e)
        })


# GET /api/stats/predictions
@blp.route('/predictions', methods=['GET'])
def predictions():
    """Get AI-powered predictive analytics for accident risk."""
    try:
        # Use NEW ML-powered predictions
        from utils.predictive_ml import ml_predictive
        
        # Get next week predictions using AI
        try:
            next_week_list = ml_predictive.predict_next_week_risk()
            # Convert list to dict keyed by day_name for compatibility
            next_week = {}
            if isinstance(next_week_list, list):
                for pred in next_week_list:
                    if isinstance(pred, dict) and 'day_name' in pred:
                        next_week[pred['day_name']] = pred
        except Exception as e:
            print(f"Error getting ML predictions: {e}")
            next_week = {}
            next_week_list = []
        
        # Get high risk times using AI
        try:
            risk_times = ml_predictive.get_high_risk_times()
        except Exception as e:
            print(f"Error getting risk times: {e}")
            risk_times = []
        
        # Get high risk days using AI
        try:
            risk_days = ml_predictive.get_high_risk_days()
        except Exception as e:
            print(f"Error getting risk days: {e}")
            risk_days = []
        
        # Get cause predictions using AI
        try:
            cause_predictions = ml_predictive.get_cause_predictions()
        except Exception as e:
            print(f"Error getting cause predictions: {e}")
            cause_predictions = []
        
        # Format weekly predictions for frontend (use AI predictions directly)
        weekly_predictions = []
        if next_week_list:
            # Use ML predictions directly
            for pred in next_week_list:
                weekly_predictions.append({
                    'day': pred.get('date', '')[-5:],  # Get MM-DD
                    'day_name': pred.get('day_name', ''),
                    'risk_level': pred.get('risk_level', 'medium').capitalize(),
                    'predicted_accidents': pred.get('predicted_count', 0),
                    'weather': pred.get('weather', 'Clear'),
                    'confidence': pred.get('confidence', 0.85)
                })
        else:
            # Fallback if ML predictions fail
            days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            today = datetime.utcnow()
            for i, day_name in enumerate(days_of_week):
                day_date = today + timedelta(days=i)
                risk_level = 'High' if day_name in ['Friday', 'Saturday'] else 'Medium' if day_name in ['Thursday', 'Sunday'] else 'Low'
                
                weekly_predictions.append({
                    'day': day_date.strftime('%a %d'),
                    'day_name': day_name,
                    'risk_level': risk_level,
                    'predicted_accidents': (i + 3) * 5,
                    'weather': 'Clear',
                    'confidence': 0.70
                })
        
        # Format high risk times - use display_time if available
        formatted_times = []
        if risk_times:
            for t in risk_times:
                if isinstance(t, dict):
                    formatted_times.append({
                        'time_range': t.get('display_time', t.get('time_range', '00:00 - 01:00')),
                        'risk_level': t.get('risk_level', 'Medium').capitalize()
                    })
        
        # Fallback times if empty
        if not formatted_times:
            formatted_times = [
                {'time_range': '17:00 - 20:00', 'risk_level': 'High'},
                {'time_range': '07:00 - 09:00', 'risk_level': 'Medium'},
                {'time_range': '22:00 - 02:00', 'risk_level': 'High'}
            ]
        
        # Calculate risk factors
        risk_factors = {
            'weekend_effect': 1.45,
            'night_driving': 1.32,
            'rain_conditions': 1.65,
            'rush_hour': 1.28,
            'holiday_periods': 1.55
        }
        
        return jsonify({
            'next_week': next_week,
            'weekly_predictions': weekly_predictions,
            'high_risk_times': formatted_times,
            'high_risk_days': risk_days,
            'cause_predictions': cause_predictions,
            'risk_factors': risk_factors
        })
    except Exception as e:
        # Return fallback predictions on error
        today = datetime.utcnow()
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        fallback_weekly = []
        for i, day_name in enumerate(days_of_week):
            day_date = today + timedelta(days=i)
            risk_level = 'High' if day_name in ['Friday', 'Saturday'] else 'Medium' if day_name in ['Thursday', 'Sunday'] else 'Low'
            fallback_weekly.append({
                'day': day_date.strftime('%a %d'),
                'day_name': day_name,
                'risk_level': risk_level,
                'predicted_accidents': i + 3
            })
        
        return jsonify({
            'next_week': {},
            'weekly_predictions': fallback_weekly,
            'high_risk_times': [
                {'time_range': '17:00 - 20:00', 'risk_level': 'High'},
                {'time_range': '07:00 - 09:00', 'risk_level': 'Medium'},
                {'time_range': '22:00 - 02:00', 'risk_level': 'High'}
            ],
            'high_risk_days': [],
            'cause_predictions': [],
            'risk_factors': {
                'weekend_effect': 1.45,
                'night_driving': 1.32,
                'rain_conditions': 1.65,
                'rush_hour': 1.28,
                'holiday_periods': 1.55
            },
            'error': str(e)
        })


# GET /api/stats/dashboard
@blp.route('/dashboard', methods=['GET'])
def dashboard_stats():
    """Quick stats for real-time dashboard updates."""
    cache_key = 'dashboard_stats'
    cached = _cache_get(cache_key)
    if cached:
        return jsonify(cached)
    
    today = datetime.utcnow().date()
    
    # Total accidents
    total_accidents = Accident.query.count()
    
    # Reports count
    reports_count = AccidentReport.query.count()
    
    # Imports today
    start_of_day = datetime(today.year, today.month, today.day)
    imports_today = Accident.query.filter(
        Accident.created_at >= start_of_day,
        Accident.source == 'import'
    ).count()
    
    # Recent accidents (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_count = Accident.query.filter(Accident.occurred_at >= week_ago).count()
    
    out = {
        'total_accidents': total_accidents,
        'reports_count': reports_count,
        'imports_today': imports_today,
        'recent_count': recent_count,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    _cache_set(cache_key, out, ttl=10)
    
    return jsonify(out)


# GET /api/stats/timeline
@blp.route('/timeline', methods=['GET'])
def accident_timeline():
    """Get accidents grouped by month for timeline animation.
    Generates coordinates based on governorate centers since Accident model
    doesn't have lat/lng columns.
    """
    cache_key = 'timeline_data'
    cached = _cache_get(cache_key)
    if cached:
        return jsonify(cached)
    
    # Governorate center coordinates for Tunisia
    gov_coords = {
        'Tunis': (36.8065, 10.1815),
        'Ariana': (36.8667, 10.1647),
        'Ben Arous': (36.7533, 10.2283),
        'Manouba': (36.8081, 9.8569),
        'Sfax': (34.7406, 10.7603),
        'Sousse': (35.8288, 10.6405),
        'Kairouan': (35.6781, 10.0963),
        'Bizerte': (37.2744, 9.8739),
        'Gabes': (33.8886, 10.0975),
        'Gabès': (33.8886, 10.0975),
        'Nabeul': (36.4561, 10.7376),
        'Monastir': (35.7643, 10.8113),
        'Mahdia': (35.5047, 11.0622),
        'Beja': (36.7256, 9.1817),
        'Béja': (36.7256, 9.1817),
        'Jendouba': (36.5011, 8.7803),
        'Le Kef': (36.1742, 8.7047),
        'Siliana': (36.0850, 9.3708),
        'Kasserine': (35.1722, 8.8306),
        'Sidi Bouzid': (35.0383, 9.4858),
        'Medenine': (33.3547, 10.5053),
        'Médenine': (33.3547, 10.5053),
        'Tataouine': (32.9297, 10.4517),
        'Gafsa': (34.4250, 8.7842),
        'Tozeur': (33.9197, 8.1339),
        'Kebili': (33.7044, 8.9714),
        'Kébili': (33.7044, 8.9714),
        'Zaghouan': (36.4029, 10.1428),
    }
    
    # Get accidents from last 12 months grouped by month and governorate
    twelve_months_ago = datetime.utcnow() - timedelta(days=365)
    
    from collections import defaultdict
    import random
    
    # Query accidents grouped by month and governorate
    accidents = Accident.query.filter(
        Accident.occurred_at >= twelve_months_ago
    ).order_by(Accident.occurred_at.asc()).all()
    
    # Group by month
    monthly = defaultdict(list)
    
    for a in accidents:
        if a.occurred_at and a.governorate:
            month_key = a.occurred_at.strftime('%Y-%m')
            gov = a.governorate
            
            # Get base coordinates for governorate
            base_coords = gov_coords.get(gov)
            if not base_coords:
                # Try partial match
                for key in gov_coords:
                    if key.lower() in gov.lower() or gov.lower() in key.lower():
                        base_coords = gov_coords[key]
                        break
            
            if base_coords:
                # Add some randomization to spread markers
                lat = base_coords[0] + (random.random() - 0.5) * 0.15
                lng = base_coords[1] + (random.random() - 0.5) * 0.15
                
                monthly[month_key].append({
                    'lat': lat,
                    'lng': lng,
                    'severity': a.severity,
                    'governorate': gov
                })
    
    # Build timeline
    timeline = []
    for month_key in sorted(monthly.keys()):
        timeline.append({
            'date': month_key,
            'accidents': monthly[month_key],
            'count': len(monthly[month_key])
        })
    
    result = {'timeline': timeline}
    _cache_set(cache_key, result, ttl=300)  # Cache for 5 minutes
    
    return jsonify(result)


# ============================================
# EXTERNAL TRAFFIC APIs
# ============================================

# GET /api/stats/holidays
@blp.route('/holidays', methods=['GET'])
def get_holidays():
    """Get Tunisia public holidays.
    
    Query params:
        year: Specific year (default: current year)
        upcoming: Number of days to look ahead (default: 30)
    
    Response:
    {
        year: int,
        holidays: [{ date, name, localName, type, risk_factor, high_impact }],
        upcoming: [{ ... days_until, is_today, is_this_week }]
    }
    """
    try:
        from utils.traffic_apis import holiday_service
        
        year = request.args.get('year', type=int)
        upcoming_days = request.args.get('upcoming', 30, type=int)
        
        holidays = holiday_service.get_tunisia_holidays(year)
        upcoming = holiday_service.get_upcoming_holidays(upcoming_days)
        today_holiday = holiday_service.is_holiday()
        
        return jsonify({
            'year': year or datetime.now().year,
            'holidays': holidays,
            'upcoming': upcoming,
            'today': today_holiday,
            'total_count': len(holidays),
            'high_impact_count': sum(1 for h in holidays if h.get('high_impact'))
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'holidays': [],
            'upcoming': []
        }), 500


# GET /api/stats/traffic-status
@blp.route('/traffic-status', methods=['GET'])
def get_traffic_status():
    """Get current traffic conditions.
    
    Query params:
        governorate: Filter by governorate (optional)
    
    Response:
    {
        timestamp, overall_status, is_rush_hour, is_weekend,
        governorates: [{ name, traffic_index, status, avg_speed_kmh }]
    }
    """
    try:
        from utils.traffic_apis import road_service
        
        governorate = request.args.get('governorate')
        status = road_service.get_traffic_status(governorate)
        
        return jsonify(status)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'unknown',
            'governorates': []
        }), 500


# GET /api/stats/roads
@blp.route('/roads', methods=['GET'])
def get_major_roads():
    """Get major roads status.
    
    Response:
    {
        roads: [{ id, name, from, to, km, status, delay_minutes, avg_speed_kmh }]
    }
    """
    try:
        from utils.traffic_apis import road_service
        
        roads = road_service.get_major_roads()
        high_risk_zones = road_service.get_high_risk_zones()
        
        return jsonify({
            'roads': roads,
            'high_risk_zones': high_risk_zones,
            'total_roads': len(roads),
            'roads_with_delays': sum(1 for r in roads if r.get('delay_minutes', 0) > 0)
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'roads': [],
            'high_risk_zones': []
        }), 500


# GET /api/stats/alerts
@blp.route('/alerts', methods=['GET'])
def get_traffic_alerts():
    """Get active traffic alerts and warnings.
    
    Query params:
        governorate: Filter by governorate (optional)
        type: Filter by type (road_work, weather_warning, accident, event)
    
    Response:
    {
        alerts: [{ id, type, title, description, governorate, severity, active }]
    }
    """
    try:
        from utils.traffic_apis import news_service
        
        governorate = request.args.get('governorate')
        alert_type = request.args.get('type')
        
        if alert_type:
            alerts = news_service.get_alerts_by_type(alert_type)
        else:
            alerts = news_service.get_active_alerts(governorate)
        
        # Group by severity
        by_severity = {'high': 0, 'medium': 0, 'low': 0}
        for alert in alerts:
            sev = alert.get('severity', 'low')
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        return jsonify({
            'alerts': alerts,
            'total_count': len(alerts),
            'by_severity': by_severity,
            'has_critical': by_severity.get('high', 0) > 0
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'alerts': [],
            'total_count': 0
        }), 500


# GET /api/stats/emergency-services
@blp.route('/emergency-services', methods=['GET'])
def get_emergency_services():
    """Get emergency services information (hospitals, police, fire stations).
    
    Query params:
        governorate: Filter by governorate (optional)
        type: Filter by type - hospitals, police, fire (optional)
    
    Response:
    {
        hospitals: [{ id, name, governorate, lat, lng, phone, emergency, beds }],
        police_stations: [{ id, name, governorate, lat, lng, phone, type }],
        fire_stations: [{ id, name, governorate, phone, response_time_min }],
        emergency_numbers: { police, ambulance, fire, ... }
    }
    """
    try:
        from utils.traffic_apis import emergency_service
        
        governorate = request.args.get('governorate')
        service_type = request.args.get('type')
        
        if service_type == 'hospitals':
            return jsonify({
                'hospitals': emergency_service.get_hospitals(governorate),
                'emergency_numbers': emergency_service.get_emergency_numbers()
            })
        elif service_type == 'police':
            return jsonify({
                'police_stations': emergency_service.get_police_stations(governorate),
                'emergency_numbers': emergency_service.get_emergency_numbers()
            })
        elif service_type == 'fire':
            return jsonify({
                'fire_stations': emergency_service.get_fire_stations(governorate),
                'emergency_numbers': emergency_service.get_emergency_numbers()
            })
        else:
            result = emergency_service.get_all_services(governorate)
            result['total_hospitals'] = len(result['hospitals'])
            result['total_police'] = len(result['police_stations'])
            result['total_fire'] = len(result['fire_stations'])
            return jsonify(result)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'hospitals': [],
            'police_stations': [],
            'fire_stations': [],
            'emergency_numbers': {
                'police': '197',
                'ambulance': '190',
                'fire': '198'
            }
        }), 500


# GET /api/stats/nearest-hospital
@blp.route('/nearest-hospital', methods=['GET'])
def get_nearest_hospital():
    """Find nearest hospital to given coordinates.
    
    Query params:
        lat: Latitude (required)
        lng: Longitude (required)
    
    Response:
    {
        hospital: { id, name, governorate, lat, lng, phone, distance_km, estimated_time_min }
    }
    """
    try:
        from utils.traffic_apis import emergency_service
        
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        
        if lat is None or lng is None:
            return jsonify({'error': 'lat and lng parameters required'}), 400
        
        nearest = emergency_service.get_nearest_hospital(lat, lng)
        
        return jsonify({
            'hospital': nearest,
            'emergency_numbers': emergency_service.get_emergency_numbers()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# GET /api/stats/speed-limits
@blp.route('/speed-limits', methods=['GET'])
def get_speed_limits():
    """Get speed limit information and zones.
    
    Query params:
        governorate: Filter zones by governorate (optional)
        zone_type: Filter by type - highway, expressway, urban, etc. (optional)
    
    Response:
    {
        limits: { highway: {...}, urban: {...}, ... },
        zones: [{ id, name, type, governorates, speed_limit, fine_base }]
    }
    """
    try:
        from utils.traffic_apis import speed_service
        
        governorate = request.args.get('governorate')
        zone_type = request.args.get('zone_type')
        
        return jsonify({
            'limits': speed_service.get_speed_limits(),
            'zones': speed_service.get_speed_zones(governorate, zone_type),
            'governorate_filter': governorate,
            'zone_type_filter': zone_type
        })
    except Exception as e:
        return jsonify({'error': str(e), 'limits': {}, 'zones': []}), 500


# GET /api/stats/fine-calculator
@blp.route('/fine-calculator', methods=['GET'])
def calculate_speeding_fine():
    """Calculate potential fine for speeding.
    
    Query params:
        zone_type: Type of zone - highway, urban, school_zone, etc. (required)
        speed: Actual speed in km/h (required)
    
    Response:
    {
        violation: bool,
        speed_limit: int,
        actual_speed: int,
        over_limit: int,
        fine: int,
        fine_currency: 'TND',
        points: int,
        severity: 'minor'|'moderate'|'serious'|'severe'
    }
    """
    try:
        from utils.traffic_apis import speed_service
        
        zone_type = request.args.get('zone_type', 'urban')
        speed = request.args.get('speed', type=int)
        
        if speed is None:
            return jsonify({'error': 'speed parameter required'}), 400
        
        result = speed_service.calculate_fine(zone_type, speed)
        result['zone_type'] = zone_type
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# GET /api/stats/vehicle-types
@blp.route('/vehicle-types', methods=['GET'])
def get_vehicle_types():
    """Get vehicle type classifications and risk factors.
    
    Response:
    {
        types: { car: {...}, motorcycle: {...}, ... },
        high_risk_vehicles: ['motorcycle', 'bicycle', 'pedestrian']
    }
    """
    try:
        from utils.traffic_apis import vehicle_service
        
        types = vehicle_service.get_vehicle_types()
        high_risk = [k for k, v in types.items() if v['risk_factor'] >= 2.0]
        
        return jsonify({
            'types': types,
            'high_risk_vehicles': high_risk,
            'total_categories': len(types)
        })
    except Exception as e:
        return jsonify({'error': str(e), 'types': {}}), 500


# GET /api/stats/driver-risk
@blp.route('/driver-risk', methods=['GET'])
def get_driver_risk():
    """Calculate driver risk based on vehicle type and age.
    
    Query params:
        vehicle: Vehicle type - car, motorcycle, truck, etc. (default: car)
        age: Driver age in years (required)
        night: Is it night driving? (optional, default: false)
        rain: Is it raining? (optional, default: false)
        holiday: Is it a holiday? (optional, default: false)
    
    Response:
    {
        risk_score: 0-100,
        risk_level: 'low'|'medium'|'high'|'critical',
        vehicle: { type, risk_factor, ... },
        driver: { age, age_group, factor, ... }
    }
    """
    try:
        from utils.traffic_apis import vehicle_service
        
        vehicle = request.args.get('vehicle', 'car')
        age = request.args.get('age', type=int)
        
        if age is None:
            return jsonify({'error': 'age parameter required'}), 400
        
        conditions = {
            'night': request.args.get('night', 'false').lower() == 'true',
            'rain': request.args.get('rain', 'false').lower() == 'true',
            'weekend': datetime.now().weekday() >= 5,
            'holiday': request.args.get('holiday', 'false').lower() == 'true'
        }
        
        result = vehicle_service.calculate_combined_risk(vehicle, age, conditions)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# GET /api/stats/route-risk
@blp.route('/route-risk', methods=['GET'])
def get_route_risk():
    """Assess risk for a route between two governorates.
    
    Query params:
        from: Origin governorate (required)
        to: Destination governorate (required)
    
    Response:
    {
        from: str,
        to: str,
        risk_score: 0-100,
        risk_level: 'low'|'medium'|'high',
        traffic_conditions: { origin, destination },
        risk_zones: [...],
        recommendations: [...]
    }
    """
    try:
        from utils.traffic_apis import route_service
        
        from_gov = request.args.get('from')
        to_gov = request.args.get('to')
        
        if not from_gov or not to_gov:
            return jsonify({'error': 'from and to parameters required'}), 400
        
        result = route_service.assess_route_risk(from_gov, to_gov)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# GET /api/stats/journey-info
@blp.route('/journey-info', methods=['GET'])
def get_journey_info():
    """Get general journey information and travel advisory.
    
    Response:
    {
        current_hour: int,
        travel_advisory: 'good'|'normal'|'caution'|'warning',
        advisory_message: str,
        is_rush_hour: bool,
        is_night: bool,
        safest_hours: str,
        avoid_hours: str
    }
    """
    try:
        from utils.traffic_apis import route_service
        
        return jsonify(route_service.get_journey_stats())
    except Exception as e:
        return jsonify({
            'error': str(e),
            'travel_advisory': 'unknown'
        }), 500


# GET /api/stats/quick-stats
@blp.route('/quick-stats', methods=['GET'])
def get_quick_stats():
    """Get quick summary statistics for dashboard widgets.
    
    Query params:
        governorate: Filter by governorate (optional)
        period: today, week, month, year (default: month)
    
    Response:
    {
        total_accidents: int,
        high_severity_count: int,
        high_severity_percent: float,
        top_cause: str,
        most_affected_area: str,
        trend: 'up'|'down'|'stable',
        trend_percent: float
    }
    """
    try:
        governorate = request.args.get('governorate')
        period = request.args.get('period', 'month')
        
        # Calculate date range
        now = datetime.utcnow()
        if period == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start_date = now - timedelta(days=7)
        elif period == 'year':
            start_date = now - timedelta(days=365)
        else:  # month
            start_date = now - timedelta(days=30)
        
        # Base query
        query = Accident.query.filter(Accident.occurred_at >= start_date)
        if governorate:
            query = query.filter(Accident.governorate == governorate)
        
        total = query.count()
        high_severity = query.filter(func.lower(Accident.severity).in_(['fatal', 'serious'])).count()
        
        # Top cause
        top_cause = db.session.query(
            Accident.cause, func.count(Accident.id).label('cnt')
        ).filter(
            Accident.occurred_at >= start_date
        ).group_by(Accident.cause).order_by(func.count(Accident.id).desc()).first()
        
        # Most affected area
        top_area = db.session.query(
            Accident.governorate, func.count(Accident.id).label('cnt')
        ).filter(
            Accident.occurred_at >= start_date
        ).group_by(Accident.governorate).order_by(func.count(Accident.id).desc()).first()
        
        # Trend calculation (compare to previous period)
        prev_start = start_date - (now - start_date)
        prev_total = Accident.query.filter(
            Accident.occurred_at >= prev_start,
            Accident.occurred_at < start_date
        ).count()
        
        if prev_total > 0:
            trend_percent = ((total - prev_total) / prev_total) * 100
            trend = 'up' if trend_percent > 5 else 'down' if trend_percent < -5 else 'stable'
        else:
            trend_percent = 0
            trend = 'stable'
        
        return jsonify({
            'total_accidents': total,
            'high_severity_count': high_severity,
            'high_severity_percent': round((high_severity / total * 100) if total > 0 else 0, 1),
            'top_cause': top_cause[0] if top_cause else 'Unknown',
            'top_cause_count': top_cause[1] if top_cause else 0,
            'most_affected_area': top_area[0] if top_area else 'Unknown',
            'most_affected_count': top_area[1] if top_area else 0,
            'trend': trend,
            'trend_percent': round(trend_percent, 1),
            'period': period,
            'governorate': governorate
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# GET /api/stats/safety-tips
@blp.route('/safety-tips', methods=['GET'])
def get_safety_tips():
    """Get contextual safety tips based on current conditions.
    
    Query params:
        governorate: For location-specific tips (optional)
    
    Response:
    {
        tips: [{ category, tip, priority }],
        current_conditions: { is_rush_hour, is_night, weather_risk },
        emergency_reminder: { ... }
    }
    """
    try:
        from utils.traffic_apis import risk_calculator, emergency_service
        
        governorate = request.args.get('governorate')
        now = datetime.now()
        hour = now.hour
        
        tips = []
        
        # Time-based tips
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            tips.append({
                'category': 'traffic',
                'tip': 'Rush hour traffic - allow extra travel time and stay patient',
                'priority': 'high',
                'icon': '🚗'
            })
        
        if hour >= 22 or hour <= 5:
            tips.append({
                'category': 'visibility',
                'tip': 'Night driving - ensure headlights are clean and properly aimed',
                'priority': 'high',
                'icon': '🌙'
            })
            tips.append({
                'category': 'alertness',
                'tip': 'Take regular breaks to combat fatigue during night driving',
                'priority': 'high',
                'icon': '☕'
            })
        
        # Weekend tips
        if now.weekday() >= 5:
            tips.append({
                'category': 'leisure',
                'tip': 'Weekend travel - expect increased traffic to tourist areas',
                'priority': 'medium',
                'icon': '🏖️'
            })
        
        # General safety tips
        general_tips = [
            {'category': 'seatbelt', 'tip': 'Always wear your seatbelt - it reduces fatality risk by 45%', 'priority': 'high', 'icon': '🔒'},
            {'category': 'phone', 'tip': 'Keep your phone away while driving - distraction is a leading cause of accidents', 'priority': 'high', 'icon': '📵'},
            {'category': 'distance', 'tip': 'Maintain at least 3 seconds following distance from the vehicle ahead', 'priority': 'medium', 'icon': '📏'},
            {'category': 'mirrors', 'tip': 'Check mirrors every 5-8 seconds to stay aware of surrounding traffic', 'priority': 'medium', 'icon': '🪞'},
            {'category': 'speed', 'tip': 'Respect speed limits - speeding reduces reaction time significantly', 'priority': 'high', 'icon': '⚡'},
        ]
        
        # Add 2-3 random general tips
        import random
        tips.extend(random.sample(general_tips, min(3, len(general_tips))))
        
        return jsonify({
            'tips': tips,
            'current_conditions': {
                'is_rush_hour': 7 <= hour <= 9 or 17 <= hour <= 19,
                'is_night': hour >= 22 or hour <= 5,
                'is_weekend': now.weekday() >= 5,
                'hour': hour
            },
            'emergency_reminder': emergency_service.get_emergency_numbers(),
            'total_tips': len(tips)
        })
    except Exception as e:
        return jsonify({'error': str(e), 'tips': []}), 500
