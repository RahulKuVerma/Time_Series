import React, { useState } from 'react';

/**
 * Interactive SVG Chart Component
 * Supports:
 * - Line series (historical actuals, predictions)
 * - Confidence bounds area (uncertainty ribbon)
 * - Interactive hover tooltips
 * - Bar charts for diurnal & categorical distributions
 */
export function TimeSeriesChart({
  historical = [],
  forecast = [],
  height = 360,
  title = "Hourly Energy Consumption & Forecast Horizon"
}) {
  const [hoverIndex, setHoverIndex] = useState(null);

  // Combine points
  const points = [];
  historical.forEach((h, idx) => {
    points.push({
      timestamp: h.timestamp,
      actual: h.actual_kWh,
      predicted: null,
      lower: null,
      upper: null,
      type: 'history'
    });
  });

  forecast.forEach((f, idx) => {
    points.push({
      timestamp: f.timestamp,
      actual: null,
      predicted: f.predicted_kWh,
      lower: f.lower_bound_kWh,
      upper: f.upper_bound_kWh,
      type: 'forecast'
    });
  });

  if (points.length === 0) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
        No time-series data available to plot.
      </div>
    );
  }

  // Find min/max values
  let minY = Infinity;
  let maxY = -Infinity;

  points.forEach(p => {
    if (p.actual !== null) {
      minY = Math.min(minY, p.actual);
      maxY = Math.max(maxY, p.actual);
    }
    if (p.predicted !== null) {
      minY = Math.min(minY, p.predicted);
      maxY = Math.max(maxY, p.predicted);
    }
    if (p.lower !== null) minY = Math.min(minY, p.lower);
    if (p.upper !== null) maxY = Math.max(maxY, p.upper);
  });

  if (minY === Infinity) minY = 0;
  if (maxY === -Infinity) maxY = 50;
  minY = Math.max(0, minY * 0.85);
  maxY = maxY * 1.15;
  const rangeY = maxY - minY || 1;

  const paddingLeft = 55;
  const paddingRight = 25;
  const paddingTop = 30;
  const paddingBottom = 45;
  const width = 950;
  const innerWidth = width - paddingLeft - paddingRight;
  const innerHeight = height - paddingTop - paddingBottom;

  const getX = (idx) => paddingLeft + (idx / (points.length - 1 || 1)) * innerWidth;
  const getY = (val) => paddingTop + innerHeight - ((val - minY) / rangeY) * innerHeight;

  // Build SVG Paths
  let histPath = "";
  let predPath = "";
  let ribbonPath = "";

  // 1. Historical Line
  let histStarted = false;
  points.forEach((p, idx) => {
    if (p.actual !== null) {
      const x = getX(idx);
      const y = getY(p.actual);
      if (!histStarted) {
        histPath += `M ${x} ${y}`;
        histStarted = true;
      } else {
        histPath += ` L ${x} ${y}`;
      }
    }
  });

  // Connect last historical to first forecast for seamless continuity
  const lastHistIdx = historical.length - 1;
  const firstFcIdx = historical.length;

  // 2. Forecast Line
  let fcStarted = false;
  if (lastHistIdx >= 0 && firstFcIdx < points.length && points[lastHistIdx].actual !== null) {
    const x0 = getX(lastHistIdx);
    const y0 = getY(points[lastHistIdx].actual);
    predPath += `M ${x0} ${y0}`;
    fcStarted = true;
  }

  points.forEach((p, idx) => {
    if (p.predicted !== null) {
      const x = getX(idx);
      const y = getY(p.predicted);
      if (!fcStarted) {
        predPath += `M ${x} ${y}`;
        fcStarted = true;
      } else {
        predPath += ` L ${x} ${y}`;
      }
    }
  });

  // 3. Uncertainty Ribbon (Upper + Lower)
  const fcPoints = points.map((p, idx) => ({ ...p, idx })).filter(p => p.upper !== null && p.lower !== null);
  if (fcPoints.length > 0) {
    let topSeq = "";
    let botSeq = "";
    fcPoints.forEach((p, i) => {
      const x = getX(p.idx);
      const yTop = getY(p.upper);
      const yBot = getY(p.lower);
      if (i === 0) {
        topSeq += `M ${x} ${yTop}`;
      } else {
        topSeq += ` L ${x} ${yTop}`;
      }
      botSeq = ` L ${x} ${yBot}` + botSeq;
    });
    ribbonPath = topSeq + botSeq + " Z";
  }

  // Y-axis grid ticks
  const yTicks = 5;
  const tickValues = [];
  for (let i = 0; i <= yTicks; i++) {
    tickValues.push(minY + (rangeY * (i / yTicks)));
  }

  // X-axis label samples (up to 7)
  const xLabelIndices = [];
  const stepInterval = Math.max(1, Math.floor(points.length / 6));
  for (let i = 0; i < points.length; i += stepInterval) {
    xLabelIndices.push(i);
  }
  if (xLabelIndices[xLabelIndices.length - 1] !== points.length - 1) {
    xLabelIndices.push(points.length - 1);
  }

  const activePoint = hoverIndex !== null && points[hoverIndex] ? points[hoverIndex] : null;

  return (
    <div style={{ position: 'relative', width: '100%', userSelect: 'none' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)' }}>{title}</h3>
        <div style={{ display: 'flex', gap: 16, fontSize: '0.8rem' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-secondary)' }}>
            <span style={{ width: 12, height: 3, background: '#3b82f6', borderRadius: 2 }}></span>
            Historical (Observed)
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--accent-emerald)' }}>
            <span style={{ width: 12, height: 3, background: 'var(--accent-emerald)', borderRadius: 2 }}></span>
            Forecast Target
          </span>
          {ribbonPath && (
            <span style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--accent-emerald)' }}>
              <span style={{ width: 12, height: 8, background: 'rgba(16, 185, 129, 0.2)', border: '1px solid rgba(16, 185, 129, 0.4)', borderRadius: 2 }}></span>
              95% Confidence Band
            </span>
          )}
        </div>
      </div>

      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: '100%', height: 'auto', overflow: 'visible' }}
        onMouseLeave={() => setHoverIndex(null)}
      >
        {/* Y-axis gridlines */}
        {tickValues.map((val, i) => {
          const y = getY(val);
          return (
            <g key={i}>
              <line x1={paddingLeft} y1={y} x2={width - paddingRight} y2={y} stroke="var(--chart-grid)" strokeDasharray="3 3" />
              <text x={paddingLeft - 8} y={y + 4} fill="var(--text-muted)" fontSize="11" textAnchor="end" fontFamily="monospace">
                {val.toFixed(1)}
              </text>
            </g>
          );
        })}

        {/* X-axis labels */}
        {xLabelIndices.map(idx => {
          const x = getX(idx);
          const p = points[idx];
          const timeShort = p ? p.timestamp.slice(5) : '';
          return (
            <g key={idx}>
              <line x1={x} y1={paddingTop + innerHeight} x2={x} y2={paddingTop + innerHeight + 5} stroke="var(--border-subtle)" />
              <text x={x} y={paddingTop + innerHeight + 18} fill="var(--text-secondary)" fontSize="10" textAnchor="middle" fontFamily="sans-serif">
                {timeShort}
              </text>
            </g>
          );
        })}

        {/* Uncertainty Ribbon */}
        {ribbonPath && (
          <path d={ribbonPath} fill="rgba(16, 185, 129, 0.15)" stroke="rgba(16, 185, 129, 0.3)" strokeWidth="1" strokeDasharray="2 2" />
        )}

        {/* Historical Line */}
        {histPath && (
          <path d={histPath} fill="none" stroke="#3b82f6" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
        )}

        {/* Forecast Line */}
        {predPath && (
          <path d={predPath} fill="none" stroke="var(--accent-emerald)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        )}

        {/* Forecast Boundary Separator */}
        {forecast.length > 0 && historical.length > 0 && (
          <line
            x1={getX(historical.length - 1)}
            y1={paddingTop}
            x2={getX(historical.length - 1)}
            y2={paddingTop + innerHeight}
            stroke="var(--accent-amber)"
            strokeWidth="1.5"
            strokeDasharray="4 4"
          />
        )}

        {/* Interactive Hover Vertical Bar */}
        {hoverIndex !== null && (
          <line
            x1={getX(hoverIndex)}
            y1={paddingTop}
            x2={getX(hoverIndex)}
            y2={paddingTop + innerHeight}
            stroke="var(--chart-cursor)"
            strokeWidth="1"
          />
        )}

        {/* Transparent Hit-Areas for mouse tracking */}
        {points.map((p, idx) => {
          const x = getX(idx);
          const w = innerWidth / points.length;
          return (
            <rect
              key={idx}
              x={x - w / 2}
              y={paddingTop}
              width={w}
              height={innerHeight}
              fill="transparent"
              style={{ cursor: 'crosshair' }}
              onMouseEnter={() => setHoverIndex(idx)}
            />
          );
        })}
      </svg>

      {/* Floating Tooltip */}
      {activePoint && hoverIndex !== null && (
        <div style={{
          position: 'absolute',
          top: 10,
          left: Math.min(Math.max(60, (getX(hoverIndex) / width) * 100), 80) + '%',
          transform: 'translateX(-50%)',
          background: 'var(--tooltip-bg)',
          border: '1px solid var(--border-subtle)',
          boxShadow: 'var(--shadow-card)',
          borderRadius: 8,
          padding: '8px 14px',
          fontSize: '0.8rem',
          pointerEvents: 'none',
          zIndex: 20,
          minWidth: 160
        }}>
          <div style={{ color: 'var(--text-secondary)', marginBottom: 4 }}>{activePoint.timestamp}</div>
          {activePoint.actual !== null && (
            <div style={{ color: '#3b82f6', fontWeight: 'bold' }}>
              Actual: {activePoint.actual.toFixed(2)} kWh
            </div>
          )}
          {activePoint.predicted !== null && (
            <div style={{ color: 'var(--accent-emerald)', fontWeight: 'bold' }}>
              Forecast: {activePoint.predicted.toFixed(2)} kWh
            </div>
          )}
          {activePoint.lower !== null && activePoint.upper !== null && (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem', marginTop: 2 }}>
              95% Band: [{activePoint.lower.toFixed(1)} - {activePoint.upper.toFixed(1)}]
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Diurnal Bar Profile Component
 */
export function DiurnalBarChart({ data = {}, buildings = [] }) {
  const hours = Array.from({ length: 24 }, (_, i) => i);
  const palette = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899'];

  return (
    <div style={{ width: '100%', overflowX: 'auto' }}>
      <div style={{ minWidth: 600, display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div style={{ display: 'flex', gap: 16, fontSize: '0.8rem', flexWrap: 'wrap' }}>
          {buildings.map((b, i) => (
            <span key={b} style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-secondary)' }}>
              <span style={{ width: 10, height: 10, borderRadius: 2, background: palette[i % palette.length] }}></span>
              {b}
            </span>
          ))}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(24, 1fr)', gap: 4, height: 180, alignItems: 'flex-end', paddingBottom: 20 }}>
          {hours.map(h => {
            return (
              <div key={h} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', justifyContent: 'flex-end' }}>
                <div style={{ display: 'flex', gap: 2, alignItems: 'flex-end', height: '100%', width: '100%' }}>
                  {buildings.map((b, i) => {
                    const val = (data[b] && data[b][h]) || 0;
                    const heightPct = Math.min(100, (val / 75) * 100);
                    return (
                      <div
                        key={b}
                        title={`${b} @ ${h}:00: ${val.toFixed(1)} kWh`}
                        style={{
                          flex: 1,
                          height: `${Math.max(4, heightPct)}%`,
                          background: palette[i % palette.length],
                          borderRadius: '2px 2px 0 0',
                          transition: 'height 0.3s ease'
                        }}
                      />
                    );
                  })}
                </div>
                <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', marginTop: 4 }}>{h}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
