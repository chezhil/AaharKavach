'use client';

import React from 'react';

// Using a basic class merging helper. 
// If `cn` from `clsx`/`tailwind-merge` is set up in `frontend/lib/utils.ts`, it should resolve correctly.
import { cn } from '@/lib/utils';
import { type NutrientStats } from '@/lib/types';

export interface NutritionLabel {
  key: string;
  label: string;
  unit: string;
}

export interface NutritionHexagonProps {
  currentStats: NutrientStats;
  userLimits: NutrientStats;
  labels: NutritionLabel[];
  className?: string;
}

export const NutritionHexagon: React.FC<NutritionHexagonProps> = ({ 
  currentStats, 
  userLimits, 
  labels,
  className 
}) => {
  // Tighten the SVG viewBox to make the inner chart scale larger natively
  const size = 340;
  const center = size / 2;
  const radius = 100; // Radius of the outermost polygon

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
  const dataPoints = labels.map((item, i) => {
    const stat = currentStats[item.key] || 0;
    const limit = userLimits[item.key] || 1; // Prevent division by zero
    
    const ratio = Math.min(stat / limit, 1.0); // Cap at 1.0 (100%)
    const isOverLimit = stat >= limit;
    
    return {
      ...item,
      ratio,
      isOverLimit,
      point: getPoint(angles[i], radius * ratio),
      labelPoint: getPoint(angles[i], radius * 1.32), // Tighter label padding
      angle: angles[i],
      statValue: stat,
      limitValue: limit,
      unit: item.unit
    };
  });

  const polygonPoints = dataPoints.map(d => `${d.point.x},${d.point.y}`).join(' ');

  return (
    <div className={cn("w-full h-full flex justify-center items-center min-h-[300px]", className)}>
      <svg 
        viewBox={`0 0 ${size} ${size}`} 
        className="w-full h-full max-w-[460px] overflow-visible font-sans"
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
              className="fill-transparent stroke-gray-300 dark:stroke-gray-600"
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
              className="stroke-gray-300 dark:stroke-gray-600"
              strokeWidth="1.5"
            />
          );
        })}

        {/* Draw Data Polygon */}
        <polygon 
          points={polygonPoints}
          className="fill-indigo-500/15 stroke-indigo-600 dark:fill-indigo-400/20 dark:stroke-indigo-400"
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
                r="3.5" 
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
                y={d.labelPoint.y - 9}
                dominantBaseline="middle"
                textAnchor={textAnchor}
                className={cn(
                  "text-[15px] md:text-base tracking-tight",
                  d.isOverLimit 
                    ? "fill-red-600 dark:fill-red-400 font-bold" 
                    : "fill-slate-900 dark:fill-white font-bold"
                )}
              >
                {d.label}
              </text>
              
              {/* Value / Limit Display */}
              <text
                x={d.labelPoint.x}
                y={d.labelPoint.y + 11}
                dominantBaseline="middle"
                textAnchor={textAnchor}
                className={cn(
                  "text-[12.5px] md:text-[13px] font-medium",
                  d.isOverLimit 
                    ? "fill-red-500/90 dark:fill-red-400/90" 
                    : "fill-gray-500 dark:fill-gray-400"
                )}
              >
                {Math.round(d.statValue)}{d.unit} / {Math.round(d.limitValue)}{d.unit}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};
