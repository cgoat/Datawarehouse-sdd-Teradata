<?php
// Gold dashboard — the 4 marts: sales performance, customer 360, product analytics,
// channel comparison. Pulls from FastAPI /gold/* endpoints.

$api = getenv('DW_API') ?: 'http://localhost:8000';

function fetch_json(string $url) {
  $ctx = stream_context_create(['http' => ['timeout' => 10, 'ignore_errors' => true]]);
  $raw = @file_get_contents($url, false, $ctx);
  if ($raw === false) return ['error' => "cannot reach $url"];
  $decoded = json_decode($raw, true);
  return is_array($decoded) ? $decoded : ['error' => 'bad json'];
}

$counts   = fetch_json("$api/gold/counts");
$summary  = fetch_json("$api/gold/sales_summary");
$top      = fetch_json("$api/gold/top_products?limit=15");
$segments = fetch_json("$api/gold/segments");
$dq       = fetch_json("$api/dq/latest?suite=gold");

function fmt_num($v): string {
  if ($v === null || $v === '') return '';
  return number_format((float)$v, 0);
}
function fmt_money($v): string {
  if ($v === null || $v === '') return '';
  return '$' . number_format((float)$v, 2);
}
function fmt_pct($v): string {
  if ($v === null || $v === '') return '';
  return number_format((float)$v * 100, 2) . '%';
}
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>DW Gold</title>
<style>
 body { font: 14px system-ui, sans-serif; margin: 24px; color: #222; }
 h1 { margin: 0 0 16px; }
 h2 { margin: 24px 0 8px; }
 nav a { margin-right: 16px; }
 table { border-collapse: collapse; margin-top: 8px; }
 th, td { text-align: left; padding: 6px 12px; border-bottom: 1px solid #eee; }
 th { background: #f5f5f5; }
 td.num { text-align: right; font-variant-numeric: tabular-nums; }
 .ok   { color: #1a7f37; font-weight: 600; }
 .fail { color: #b4252a; font-weight: 600; }
 .muted { color: #666; }
 .err { background: #fdecec; padding: 10px; border: 1px solid #f5a5a5; }
 .row { display: flex; gap: 32px; flex-wrap: wrap; }
 .card { flex: 1 1 380px; }
</style>
</head>
<body>
<h1>Gold</h1>
<nav>
  <a href="index.php">Reliability</a>
  <a href="silver.php">Silver</a>
  <a href="gold.php">Gold</a>
  <a href="perf.php">Performance</a>
  <span class="muted">|  4 marts (Phase 2): sales perf, customer 360, product analytics, channel comparison</span>
</nav>

<div class="row">
  <div class="card">
    <h2>Mart row counts</h2>
    <?php if (!empty($counts['error'])): ?>
      <div class="err"><?= htmlspecialchars($counts['error']) ?></div>
    <?php else: ?>
    <table>
      <tr><th>Mart</th><th>Rows</th></tr>
      <?php foreach ($counts as $c): ?>
        <tr>
          <td><?= htmlspecialchars($c['table'] ?? '') ?></td>
          <td class="num">
            <?php if (($c['row_count'] ?? null) === null): ?>
              <span class="fail" title="<?= htmlspecialchars($c['error'] ?? '') ?>">ERR</span>
            <?php else: ?>
              <?= number_format((int)$c['row_count']) ?>
            <?php endif; ?>
          </td>
        </tr>
      <?php endforeach; ?>
    </table>
    <?php endif; ?>
  </div>

  <div class="card">
    <h2>Sales by channel (lifetime)</h2>
    <?php if (!empty($summary['error'])): ?>
      <div class="err"><?= htmlspecialchars($summary['error']) ?></div>
    <?php else: ?>
    <table>
      <tr><th>Channel</th><th>Units</th><th>Orders</th><th>Gross</th><th>Net</th><th>Profit</th><th>Returns</th></tr>
      <?php foreach (($summary['by_channel'] ?? []) as $r): ?>
        <tr>
          <td><strong><?= htmlspecialchars($r['channel'] ?? '') ?></strong></td>
          <td class="num"><?= fmt_num($r['units_sold']  ?? null) ?></td>
          <td class="num"><?= fmt_num($r['order_count'] ?? null) ?></td>
          <td class="num"><?= fmt_money($r['gross_sales']    ?? null) ?></td>
          <td class="num"><?= fmt_money($r['net_sales']      ?? null) ?></td>
          <td class="num"><?= fmt_money($r['net_profit']     ?? null) ?></td>
          <td class="num"><?= fmt_money($r['returns_amount'] ?? null) ?></td>
        </tr>
      <?php endforeach; ?>
    </table>
    <?php endif; ?>
  </div>
</div>

<div class="row">
  <div class="card">
    <h2>Top 15 products by revenue</h2>
    <?php if (!empty($top['error']) || (count($top) > 0 && !empty($top[0]['error']))): ?>
      <div class="err"><?= htmlspecialchars($top['error'] ?? $top[0]['error']) ?></div>
    <?php else: ?>
    <table>
      <tr><th>#</th><th>Product</th><th>Brand</th><th>Category</th><th>Units</th><th>Revenue</th><th>Returns</th><th>Top channel</th></tr>
      <?php foreach ($top as $p): ?>
        <tr>
          <td class="num"><?= htmlspecialchars((string)($p['rank_by_revenue'] ?? '')) ?></td>
          <td><?= htmlspecialchars($p['product_name'] ?? '') ?></td>
          <td><?= htmlspecialchars($p['brand'] ?? '') ?></td>
          <td><?= htmlspecialchars($p['category'] ?? '') ?></td>
          <td class="num"><?= fmt_num($p['units_sold']    ?? null) ?></td>
          <td class="num"><?= fmt_money($p['gross_revenue'] ?? null) ?></td>
          <td class="num"><?= fmt_pct($p['returns_rate']  ?? null) ?></td>
          <td><?= htmlspecialchars($p['top_channel'] ?? '') ?></td>
        </tr>
      <?php endforeach; ?>
    </table>
    <?php endif; ?>
  </div>

  <div class="card">
    <h2>Customer segments (RFM)</h2>
    <?php if (!empty($segments['error']) || (count($segments) > 0 && !empty($segments[0]['error']))): ?>
      <div class="err"><?= htmlspecialchars($segments['error'] ?? $segments[0]['error']) ?></div>
    <?php else: ?>
    <table>
      <tr><th>Segment</th><th>Customers</th><th>Avg LTV</th><th>Avg freq</th><th>Avg recency</th></tr>
      <?php foreach ($segments as $s): ?>
        <tr>
          <td><strong><?= htmlspecialchars($s['segment'] ?? '') ?></strong></td>
          <td class="num"><?= fmt_num($s['customers']         ?? null) ?></td>
          <td class="num"><?= fmt_money($s['avg_ltv']         ?? null) ?></td>
          <td class="num"><?= fmt_num($s['avg_frequency']     ?? null) ?></td>
          <td class="num"><?= fmt_num($s['avg_recency_days']  ?? null) ?>d</td>
        </tr>
      <?php endforeach; ?>
    </table>
    <?php endif; ?>
  </div>
</div>

<h2>Gold DQ (latest batch)</h2>
<?php if (!empty($dq['error'])): ?>
  <div class="err"><?= htmlspecialchars($dq['error']) ?></div>
<?php elseif (count($dq) === 0): ?>
  <p class="muted">No DQ results yet.</p>
<?php else: ?>
<table>
  <tr><th>Table</th><th>Expectation</th><th>Result</th><th>Observed</th><th>Run at</th></tr>
  <?php foreach ($dq as $d): ?>
    <tr>
      <td><?= htmlspecialchars($d['table_name'] ?? '') ?></td>
      <td><?= htmlspecialchars($d['expectation'] ?? '') ?></td>
      <td class="<?= ($d['success'] ?? 0) ? 'ok' : 'fail' ?>">
        <?= ($d['success'] ?? 0) ? 'PASS' : 'FAIL' ?>
      </td>
      <td><?= htmlspecialchars(substr((string)($d['observed_value'] ?? ''), 0, 80)) ?></td>
      <td><?= htmlspecialchars($d['run_at'] ?? '') ?></td>
    </tr>
  <?php endforeach; ?>
</table>
<?php endif; ?>

</body>
</html>
