import React from 'react';

interface ChartData {
  date: string;
  biomass: number;
  rainfall: number;
}

interface BiomassChartProps {
  data: ChartData[];
  type: 'biomass' | 'rainfall';
  color: string;
  showGrid?: boolean;
  showPoints?: boolean;
  unitLabel?: string;
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
};

const RainfallChart: React.FC<{ data: ChartData[]; color: string }> = ({ data, color }) => {
  const maxValue = Math.max(...data.map(d => d.rainfall)) || 1;

  return (
    <div className="w-full h-64 p-4 bg-white dark:bg-zinc-900 rounded-lg shadow-sm">
      <div className="flex items-end justify-between h-full space-x-2">
        {data.map((item, index) => {
          const height = (item.rainfall / maxValue) * 100;
          return (
            <div key={index} className="flex flex-col items-center flex-1 group">
              <div className="text-xs text-muted-foreground mb-1 opacity-80 group-hover:opacity-100 transition">
                {item.rainfall.toFixed(1)}mm
              </div>
              <div
                className="w-full rounded-md transition-all duration-500 ease-out shadow-sm group-hover:shadow-md"
                style={{
                  height: `${height}%`,
                  background: `linear-gradient(to top, ${color}, ${color}80)`,
                  minHeight: '4px',
                }}
              />
              <div className="text-xs text-muted-foreground mt-2 text-center">
                {formatDate(item.date)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const BiomassLineChart: React.FC<{
  data: ChartData[];
  color: string;
  showGrid?: boolean;
  showPoints?: boolean;
  unitLabel?: string;
}> = ({ data, color, showGrid = true, showPoints = true, unitLabel = 'g/m²' }) => {
  const values = data.map(d => d.biomass);
  const maxValue = Math.max(...values);
  const minValue = Math.min(...values);
  const range = maxValue - minValue || 1;

  const points = data.map((item, index) => {
    const x = (index / (data.length - 1)) * 100;
    const y = 100 - ((item.biomass - minValue) / range) * 100;
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className="w-full h-64 p-4 bg-white dark:bg-zinc-900 rounded-lg shadow-sm">
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        role="img"
        aria-label="Biomass trend line chart"
      >
        <title>Biomass Trend</title>

        {showGrid &&
          [0, 25, 50, 75, 100].map(y => (
            <line
              key={y}
              x1="0"
              y1={y}
              x2="100"
              y2={y}
              stroke="hsl(var(--muted))"
              strokeWidth="0.3"
              opacity="0.3"
            />
          ))}

        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="transition-all duration-1000 ease-out"
        />

        {showPoints &&
          data.map((item, index) => {
            const x = (index / (data.length - 1)) * 100;
            const y = 100 - ((item.biomass - minValue) / range) * 100;
            return (
              <circle
                key={index}
                cx={x}
                cy={y}
                r="1.5"
                fill={color}
                className="transition-all duration-1000 ease-out"
              >
                <title>{`${item.biomass.toFixed(1)} ${unitLabel}`}</title>
              </circle>
            );
          })}
      </svg>

      <div className="flex justify-between mt-2">
        {data.map((item, index) => (
          <div key={index} className="text-xs text-muted-foreground text-center flex-1">
            {formatDate(item.date)}
          </div>
        ))}
      </div>

      <div className="flex justify-between mt-2 text-xs text-muted-foreground">
        <span>{minValue.toFixed(1)} {unitLabel}</span>
        <span>{maxValue.toFixed(1)} {unitLabel}</span>
      </div>
    </div>
  );
};

export const BiomassChart: React.FC<BiomassChartProps> = ({
  data,
  type,
  color,
  showGrid,
  showPoints,
  unitLabel,
}) => {
  return type === 'rainfall' ? (
    <RainfallChart data={data} color={color} />
  ) : (
    <BiomassLineChart
      data={data}
      color={color}
      showGrid={showGrid}
      showPoints={showPoints}
      unitLabel={unitLabel}
    />
  );
};