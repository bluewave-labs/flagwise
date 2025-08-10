import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';

const Anomalies = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Anomalies</h1>
        <p className="text-13 text-gray-600">
          Detect volume spikes, new models, and reused prompts
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Coming Soon</CardTitle>
          <CardDescription>
            This page will show anomaly detection results
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-2">
            <Badge variant="secondary">Under Development</Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Anomalies;