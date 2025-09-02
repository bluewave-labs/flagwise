import React from 'react';
import { cn } from '../../lib/utils';

const Skeleton = ({ className, ...props }) => {
  return (
    <div
      className={cn(
        "animate-pulse rounded bg-muted",
        className
      )}
      {...props}
    />
  );
};

const SkeletonCard = ({ className }) => {
  return (
    <div className={cn("rounded border bg-card shadow-sm", className)}>
      <div className="p-6 space-y-3">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
        <Skeleton className="h-8 w-full" />
      </div>
    </div>
  );
};

const SkeletonMetricCard = ({ className, variant }) => {
  const variantClasses = {
    blue: "border-l-4 border-l-blue-500 bg-blue-50/30",
    red: "border-l-4 border-l-red-500 bg-red-50/30",
    green: "border-l-4 border-l-green-500 bg-green-50/30",
    orange: "border-l-4 border-l-orange-500 bg-orange-50/30",
    purple: "border-l-4 border-l-purple-500 bg-purple-50/30",
    default: "border-l-4 border-l-gray-500 bg-gray-50/30"
  };

  return (
    <div className={cn(
      "rounded border bg-card shadow-sm p-6",
      variant && variantClasses[variant],
      className
    )}>
      <div className="flex items-center space-x-3">
        <Skeleton className="h-5 w-5 rounded" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-6 w-16" />
        </div>
      </div>
    </div>
  );
};

const SkeletonTable = ({ rows = 5, columns = 4, className }) => {
  return (
    <div className={cn("rounded-md border", className)}>
      {/* Header */}
      <div className="border-b p-4">
        <div className="flex space-x-4">
          {Array.from({ length: columns }).map((_, i) => (
            <Skeleton key={i} className="h-4 flex-1" />
          ))}
        </div>
      </div>
      
      {/* Rows */}
      <div className="divide-y">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="p-4">
            <div className="flex space-x-4">
              {Array.from({ length: columns }).map((_, j) => (
                <Skeleton key={j} className="h-4 flex-1" />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const SkeletonChart = ({ height = 300, className }) => {
  return (
    <div className={cn("space-y-4", className)} style={{ height }}>
      {/* Chart title area */}
      <div className="space-y-2">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-3 w-48" />
      </div>
      
      {/* Chart area with bars/lines simulation */}
      <div className="flex items-end justify-between space-x-2" style={{ height: height - 60 }}>
        {Array.from({ length: 8 }).map((_, i) => {
          const randomHeight = Math.random() * 0.8 + 0.2; // 20% to 100% height
          return (
            <Skeleton
              key={i}
              className="flex-1"
              style={{ height: `${randomHeight * 100}%` }}
            />
          );
        })}
      </div>
      
      {/* X-axis labels */}
      <div className="flex justify-between">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-3 w-8" />
        ))}
      </div>
    </div>
  );
};

const SkeletonList = ({ items = 5, className }) => {
  return (
    <div className={cn("space-y-3", className)}>
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="flex items-center space-x-3 p-3 border rounded-lg">
          <Skeleton className="h-10 w-10 rounded" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
          <Skeleton className="h-8 w-20" />
        </div>
      ))}
    </div>
  );
};

const SkeletonDashboard = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96" />
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <SkeletonMetricCard variant="blue" />
        <SkeletonMetricCard variant="red" />
        <SkeletonMetricCard variant="orange" />
        <SkeletonMetricCard variant="green" />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SkeletonCard>
          <div className="p-6">
            <div className="space-y-4">
              <div className="space-y-2">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-3 w-48" />
              </div>
              <SkeletonList items={4} />
            </div>
          </div>
        </SkeletonCard>
        
        <SkeletonCard>
          <div className="p-6">
            <div className="space-y-4">
              <div className="space-y-2">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-3 w-48" />
              </div>
              <SkeletonList items={4} />
            </div>
          </div>
        </SkeletonCard>
      </div>

      {/* Recent Activity */}
      <SkeletonCard>
        <div className="p-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-3 w-32" />
            </div>
            <SkeletonList items={6} />
          </div>
        </div>
      </SkeletonCard>
    </div>
  );
};

const SkeletonAnalytics = () => {
  return (
    <div className="space-y-6">
      {/* Header with controls */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-80" />
        </div>
        <Skeleton className="h-9 w-24" />
      </div>

      {/* Filters Card */}
      <SkeletonCard>
        <div className="p-6">
          <div className="space-y-4">
            <Skeleton className="h-5 w-40" />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="space-y-2">
                  <Skeleton className="h-3 w-16" />
                  <Skeleton className="h-9 w-full" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </SkeletonCard>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <SkeletonMetricCard variant="blue" />
        <SkeletonMetricCard variant="red" />
        <SkeletonMetricCard variant="orange" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SkeletonCard>
          <div className="p-6">
            <SkeletonChart height={300} />
          </div>
        </SkeletonCard>
        
        <SkeletonCard>
          <div className="p-6">
            <SkeletonChart height={300} />
          </div>
        </SkeletonCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SkeletonCard>
          <div className="p-6">
            <SkeletonChart height={300} />
          </div>
        </SkeletonCard>
        
        <SkeletonCard>
          <div className="p-6">
            <SkeletonChart height={300} />
          </div>
        </SkeletonCard>
      </div>
    </div>
  );
};

const SkeletonUserTable = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-80" />
        </div>
        <Skeleton className="h-9 w-24" />
      </div>

      {/* Filters */}
      <SkeletonCard>
        <div className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-3 w-16" />
                <Skeleton className="h-9 w-full" />
              </div>
            ))}
          </div>
        </div>
      </SkeletonCard>

      {/* Table */}
      <SkeletonTable rows={8} columns={7} />

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-32" />
        <div className="flex space-x-2">
          <Skeleton className="h-9 w-20" />
          <Skeleton className="h-9 w-8" />
          <Skeleton className="h-9 w-8" />
          <Skeleton className="h-9 w-20" />
        </div>
      </div>
    </div>
  );
};

const SkeletonForm = ({ fields = 4 }) => {
  return (
    <div className="space-y-6">
      {Array.from({ length: fields }).map((_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-10 w-full" />
          {Math.random() > 0.5 && <Skeleton className="h-3 w-3/4" />}
        </div>
      ))}
      
      <div className="flex justify-end space-x-2 pt-4">
        <Skeleton className="h-9 w-20" />
        <Skeleton className="h-9 w-24" />
      </div>
    </div>
  );
};

const SkeletonDetectionRules = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="flex items-center space-x-3">
          <Skeleton className="h-9 w-28" />
          <Skeleton className="h-9 w-32" />
        </div>
      </div>

      {/* Filters Card */}
      <SkeletonCard>
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-4 w-32" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-3 w-16" />
                <Skeleton className="h-9 w-full" />
              </div>
            ))}
          </div>
        </div>
      </SkeletonCard>

      {/* Rules Table */}
      <div className="space-y-4">
        <Skeleton className="h-6 w-40" />
        <div className="rounded-md border">
          {/* Table Header */}
          <div className="border-b p-4">
            <div className="flex space-x-4">
              <Skeleton className="h-4 w-4" />
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-4 w-18" />
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-4 w-18" />
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-4 w-20" />
            </div>
          </div>
          
          {/* Table Rows */}
          <div className="divide-y">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="p-4">
                <div className="flex space-x-4">
                  <Skeleton className="h-4 w-4" />
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center space-x-2">
                      <Skeleton className="h-4 w-4" />
                      <Skeleton className="h-4 w-32" />
                    </div>
                    <Skeleton className="h-3 w-48" />
                    <Skeleton className="h-6 w-64" />
                  </div>
                  <Skeleton className="h-6 w-20" />
                  <Skeleton className="h-6 w-16" />
                  <Skeleton className="h-6 w-18" />
                  <Skeleton className="h-4 w-12" />
                  <Skeleton className="h-4 w-12" />
                  <Skeleton className="h-6 w-16" />
                  <Skeleton className="h-8 w-8" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-32" />
        <div className="flex space-x-2">
          <Skeleton className="h-9 w-20" />
          <Skeleton className="h-9 w-8" />
          <Skeleton className="h-9 w-8" />
          <Skeleton className="h-9 w-20" />
        </div>
      </div>
    </div>
  );
};

const SkeletonSettings = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-80" />
        </div>
        <Skeleton className="h-9 w-24" />
      </div>

      {/* Tabs */}
      <div className="space-y-6">
        <div className="flex space-x-1 bg-muted rounded-lg p-1 w-fit">
          <Skeleton className="h-9 w-32" />
          <Skeleton className="h-9 w-32" />
        </div>

        {/* Data Sources Tab Content */}
        <div className="space-y-6">
          {/* Demo Data Control */}
          <SkeletonCard>
            <div className="p-6">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Skeleton className="h-5 w-40" />
                  <Skeleton className="h-4 w-64" />
                </div>
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-3 w-48" />
                  </div>
                  <Skeleton className="h-9 w-32" />
                </div>
              </div>
            </div>
          </SkeletonCard>

          {/* Kafka Configuration */}
          <SkeletonCard>
            <div className="p-6">
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-2">
                    <Skeleton className="h-5 w-40" />
                    <Skeleton className="h-4 w-96" />
                  </div>
                  <div className="flex items-center space-x-2">
                    <Skeleton className="h-3 w-3 rounded-full" />
                    <Skeleton className="h-4 w-20" />
                  </div>
                </div>

                {/* Connection Settings */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="space-y-2">
                      <Skeleton className="h-4 w-24" />
                      <Skeleton className="h-10 w-full" />
                      <Skeleton className="h-3 w-32" />
                    </div>
                  ))}
                </div>

                {/* Advanced Settings */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Array.from({ length: 2 }).map((_, i) => (
                    <div key={i} className="space-y-2">
                      <Skeleton className="h-4 w-32" />
                      <Skeleton className="h-10 w-full" />
                    </div>
                  ))}
                </div>

                {/* Schema Section */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-28" />
                    <Skeleton className="h-48 w-full" />
                  </div>
                  <div className="p-4 bg-muted/20 rounded-lg space-y-3">
                    <Skeleton className="h-4 w-32" />
                    {Array.from({ length: 6 }).map((_, i) => (
                      <div key={i} className="flex items-start space-x-2">
                        <Skeleton className="h-5 w-16" />
                        <Skeleton className="h-3 w-40" />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center justify-between pt-4 border-t">
                  <Skeleton className="h-9 w-32" />
                  <div className="space-x-2 flex">
                    <Skeleton className="h-9 w-20" />
                    <Skeleton className="h-9 w-36" />
                  </div>
                </div>
              </div>
            </div>
          </SkeletonCard>
        </div>
      </div>
    </div>
  );
};

export {
  Skeleton,
  SkeletonCard,
  SkeletonMetricCard,
  SkeletonTable,
  SkeletonChart,
  SkeletonList,
  SkeletonDashboard,
  SkeletonAnalytics,
  SkeletonUserTable,
  SkeletonForm,
  SkeletonDetectionRules,
  SkeletonSettings
};