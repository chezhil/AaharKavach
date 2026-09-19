'use client';

import React from 'react';

// Using a basic class merging helper. 
// If `cn` from `clsx`/`tailwind-merge` is set up in `frontend/lib/utils.ts`, it should resolve correctly.
import { cn } from '@/lib/utils';
import { type NutrientStats } from '@/lib/types';

export interface NutritionHexagonProps {
  currentStats: NutrientStats;
  userLimits: NutrientStats;
  className?: string;
}

const LABELS = [
  { key: 'Energy_kcal', label: 'Energy' },
  { key: 'Protein', label: 'Protein' },
  { key: 'Carbs', label: 'Carbs' },
  { key: 'Sugars', label: 'Sugars' },
  { key: 'Fat', label: 'Fat' },
  { key: 'Salt', label: 'Salt/Sodium' },
] as const;

export const NutritionHexagon: React.FC<NutritionHexagonProps> = ({ 
  currentStats, 
  userLimits, 
  className 
}) => {
  const size = 300;
  const center = size / 2;
  const radius = 100; // Leaves space for labels around the hexagon

  // Angles in radians starting from top (-90 deg) and going clockwise
  const angles = [
    -Math.PI / 2,         // Top (Energy)
    -Math.PI / 6,         // Top Right (Protein)
    Math.PI / 6,          // Bottom Right (Carbs)
    Math.PI / 2,          // Bottom (Sugars)
    5 * Math.PI / 6,      // Bottom Left (Fat)
    7 * Math.PI / 6,      // Top Left (Salt)
  ];

  // Helper to convert polar coordinates to cartesian
  const getPoint = (angle: number, r: number) => {
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle)
    };
  };

  // Generate background web lines (3 concentric hexagons)
  const webLevels = [0.33, 0.66, 1.0];

  // Calculate coordinates for the actual data polygon
  const dataPoints = LABELS.map((item, i) => {
    const stat = currentStats[item.key] || 0;
    const limit = userLimits[item.key] || 1; // Prevent division by zero
    
    const ratio = Math.min(stat / limit, 1.0); // Cap at 1.0 (100%)
    const isOverLimit = stat >= limit;
    
    return {
      ...item,
      ratio,
      isOverLimit,
      point: getPoint(angles[i], radius * ratio),
      labelPoint: getPoint(angles[i], radius * 1.3), // Push labels slightly outside
      angle: angles[i],
      statValue: stat,
      limitValue: limit
    };
  });

  const polygonPoints = dataPoints.map(d => `${d.point.x},${d.point.y}`).join(' ');

  return (
    <div className={cn("w-full h-full flex justify-center items-center min-h-[300px]", className)}>
      <svg 
        viewBox={`0 0 ${size} ${size}`} 
        className="w-full h-full max-w-[400px] overflow-visible font-sans"
      >
        
        {/* Draw Web (Concentric Hexagons) */}
        {webLevels.map(level => {
          const points = angles.map(a => {
            const p = getPoint(a, radius * level);
            return `${p.x},${p.y}`;
          }).join(' ');
          
          return (
            <polygon 
              key={level}
              points={points}
              className="fill-transparent stroke-gray-200 dark:stroke-gray-800"
              strokeWidth="1.5"
            />
          );
        })}

        {/* Draw Axes (Lines from center to vertices) */}
        {angles.map((a, i) => {
          const p = getPoint(a, radius);
          return (
            <line 
              key={i}
              x1={center} y1={center}
              x2={p.x} y2={p.y}
              className="stroke-gray-200 dark:stroke-gray-800"
              strokeWidth="1.5"
            />
          );
        })}

        {/* Draw Data Polygon */}
        <polygon 
          points={polygonPoints}
          className="fill-indigo-500/30 stroke-indigo-600 dark:fill-indigo-400/40 dark:stroke-indigo-400"
          strokeWidth="2.5"
          strokeLinejoin="round"
        />

        {/* Draw Data Points & Labels */}
        {dataPoints.map((d) => {
          // Adjust text anchoring based on the angle so labels push outward properly
          let textAnchor = "middle";
          if (d.angle > -Math.PI / 2 && d.angle < Math.PI / 2) textAnchor = "start";
          else if (d.angle > Math.PI / 2 || d.angle < -Math.PI / 2) textAnchor = "end";

          return (
            <g key={d.key}>
              {/* Vertex Point */}
              <circle 
                cx={d.point.x} 
                cy={d.point.y} 
                r="4.5" 
                className={cn(
                  "transition-colors duration-300",
                  d.isOverLimit 
                    ? "fill-red-500 dark:fill-red-400" 
                    : "fill-indigo-600 dark:fill-indigo-400"
                )}
              />
              
              {/* Label Name */}
              <text
                x={d.labelPoint.x}
                y={d.labelPoint.y}
                dominantBaseline="middle"
                textAnchor={textAnchor}
                className={cn(
                  "text-[13px] md:text-sm font-medium tracking-tight",
                  d.isOverLimit 
                    ? "fill-red-600 dark:fill-red-400 font-bold" 
                    : "fill-slate-700 dark:fill-slate-300"
                )}
              >
                {d.label}
              </text>
              
              {/* Value / Limit Display */}
              <text
                x={d.labelPoint.x}
                y={d.labelPoint.y + 16}
                dominantBaseline="middle"
                textAnchor={textAnchor}
                className={cn(
                  "text-[11px]",
                  d.isOverLimit 
                    ? "fill-red-500/90 dark:fill-red-400/90" 
                    : "fill-slate-500 dark:fill-slate-400"
                )}
              >
                {Math.round(d.statValue)} / {Math.round(d.limitValue)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};
