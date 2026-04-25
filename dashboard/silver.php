<?php
// Silver dashboard — row counts across dims/facts and anomaly breakdown.
// Pulls from the same FastAPI helper as index.php.

$api = getenv('DW_API') ?: 'http://localhost:8000';

function fetch_json(string $url): array {
  $ctx = stream_context_create(['http' => ['timeout' => 10, 'ignore_errors' => true]]);
  $raw = @file_get_contents($url, false, $ctx);
  if ($raw === false) return ['error' => "cannot reach $url"];
  $decoded = json_decode($raw, true);
  return is_array($decoded) ? $decoded : ['error' => 'bad json'];
}

$counts    = fetch_json("$api/silver/counts");
$anomalies = fetch_json("$api/silver/anomaly_breakdown");
$dq        = fetch_json("$api/dq/latest?suite=silver");
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>DW Silver</title>
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
<h1>Silver</h1>
<nav>
  <a href="index.php">Reliability</a>
  <a href="silver.php">Silver</a>
  <a href="gold.php">Gold</a>
  <a href="perf.php">Performance</a>
  <span class="muted">|  Conformed dims + unified facts + anomaly sidecars (Phase 1)</span>
</nav>

<div class="row">
  <div class="card">
    <h2>Row counts</h2>
    <?php if (!empty($counts['error'])): ?>
      <div class="err"><?= htmlspecialchars($counts['error']) ?></div>
    <?php else: ?>
    <table>
      <tr><th>Table</th><th>Rows</th></tr>
      <?php foreach ($counts as $c): ?>
        <tr>
          <td><?= htmlspecialchars($c['table'] ?? '') ?></td>
          <td class="num">
            <?php if (($c['row_count'] ?? null) === null): ?>
              <span class="fail">ERR</span>
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
    <h2>Anomaly breakdown</h2>
    <?php if (!empty($anomalies['error'])): ?>
      <div class="err"><?= htmlspecialchars($anomalies['error']) ?></div>
    <?php elseif (count($anomalies) === 0): ?>
      <p class="muted">No anomalies recorded.</p>
    <?php else: ?>
    <table>
      <tr><th>Source</th><th>Reason</th><th>Count</th></tr>
      <?php foreach ($anomalies as $a): ?>
        <?php if (!empty($a['error'])): ?>
          <tr><td colspan="3" class="err"><?= htmlspecialchars($a['error']) ?></td></tr>
        <?php else: ?>
        <tr>
          <td><?= htmlspecialchars($a['source_table'] ?? '') ?></td>
          <td><?= htmlspecialchars($a['_anomaly_reason'] ?? '') ?></td>
          <td class="num"><?= number_format((int)($a['cnt'] ?? 0)) ?></td>
        </tr>
        <?php endif; ?>
      <?php endforeach; ?>
    </table>
    <?php endif; ?>
  </div>
</div>

<h2>Silver DQ (latest batch)</h2>
<?php if (!empty($dq['error'])): ?>
  <div class="err"><?= htmlspecialchars($dq['error']) ?></div>
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
