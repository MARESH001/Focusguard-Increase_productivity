import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  Monitor, 
  Play, 
  Stop, 
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Clock
} from 'lucide-react';

const RealWindowMonitor = ({ user, apiBaseUrl, isBackendAvailable }) => {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [currentWindow, setCurrentWindow] = useState('Unknown');
  const [sessionId, setSessionId] = useState(null);
  const [lastActivity, setLastActivity] = useState(null);
  const [activityHistory, setActivityHistory] = useState([]);
  const [monitoringStats, setMonitoringStats] = useState({
    startTime: null,
    windowChanges: 0,
    distractions: 0,
    productive: 0
  });
  
  const [lastWindowTitle, setLastWindowTitle] = useState(''); // Track last logged window title
  
  const monitoringIntervalRef = useRef(null);
  const sessionRef = useRef(null);

  useEffect(() => {
    return () => {
      if (monitoringIntervalRef.current) {
        clearInterval(monitoringIntervalRef.current);
      }
    };
  }, []);

  const createFocusSession = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/users/${user.username}/sessions/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_description: "Real-time window monitoring",
          keywords: ["monitoring", "focus", "productivity"],
          duration_minutes: 60
        }),
      });

      if (response.ok) {
        const sessionData = await response.json();
        setSessionId(sessionData.id);
        sessionRef.current = sessionData.id;
        return sessionData.id;
      } else {
        console.error('Failed to create session');
        return null;
      }
    } catch (error) {
      console.error('Error creating session:', error);
      return null;
    }
  };

  const getCurrentWindowInfo = async () => {
    try {
      // This would normally call a native function or use a desktop API
      // For now, we'll simulate it and show how it should work
      
      // In a real implementation, this would call:
      // - Windows: GetForegroundWindow() + GetWindowText()
      // - macOS: [NSWorkspace sharedWorkspace].activeApplication
      // - Linux: xdotool getactivewindow getwindowname
      
      const mockWindowInfo = {
        title: `Simulated Window - ${new Date().toLocaleTimeString()}`,
        process: 'chrome.exe',
        fullTitle: `chrome.exe - Simulated Window - ${new Date().toLocaleTimeString()}`
      };
      
      return mockWindowInfo;
    } catch (error) {
      console.error('Error getting window info:', error);
      return {
        title: 'Error Getting Window',
        process: 'Unknown',
        fullTitle: 'Error Getting Window'
      };
    }
  };

  const logActivity = async (windowTitle) => {
    if (!sessionRef.current) return;
    
    // This now calls the enhanced endpoint which sends notifications for distractions

    try {
      const response = await fetch(`${apiBaseUrl}/sessions/${sessionRef.current}/activity/enhanced`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionRef.current,
          window_title: windowTitle
        }),
      });

      if (response.ok) {
        const result = await response.json();
        const activity = {
          id: result.id,
          windowTitle: windowTitle,
          classification: result.classification,
          isDistraction: result.is_distraction,
          confidence: result.confidence,
          timestamp: new Date(result.timestamp),
          confidenceColor: result.is_distraction ? 'text-red-500' : 'text-green-500'
        };
        
        setLastActivity(activity);
        setActivityHistory(prev => [activity, ...prev.slice(0, 9)]); // Keep last 10
        
        // Update stats
        setMonitoringStats(prev => ({
          ...prev,
          windowChanges: prev.windowChanges + 1,
          distractions: prev.distractions + (result.is_distraction ? 1 : 0),
          productive: prev.productive + (result.is_distraction ? 0 : 1)
        }));
        
        return result;
      } else {
        console.error('Failed to log activity');
        return null;
      }
    } catch (error) {
      console.error('Error logging activity:', error);
      return null;
    }
  };

  const startMonitoring = async () => {
    if (!isBackendAvailable) {
      alert('Backend is not available. Please check your connection.');
      return;
    }

    const sessionId = await createFocusSession();
    if (!sessionId) {
      alert('Failed to create monitoring session');
      return;
    }

    setIsMonitoring(true);
    setMonitoringStats(prev => ({
      ...prev,
      startTime: new Date(),
      windowChanges: 0,
      distractions: 0,
      productive: 0
    }));
    setLastWindowTitle(''); // Reset window title tracking

    // Start monitoring interval - only log when window actually changes
    monitoringIntervalRef.current = setInterval(async () => {
      const windowInfo = await getCurrentWindowInfo();
      const newWindowTitle = windowInfo.fullTitle;
      
      // Only log activity if window title has actually changed from last logged title
      if (newWindowTitle !== lastWindowTitle) {
        setCurrentWindow(newWindowTitle);
        setLastWindowTitle(newWindowTitle);
        console.log('Window changed, logging activity:', newWindowTitle);
        await logActivity(newWindowTitle);
      } else {
        // Just update the display, don't log to API
        setCurrentWindow(newWindowTitle);
      }
    }, 2000); // Check every 2 seconds

    console.log('Started real window monitoring');
  };

  const stopMonitoring = () => {
    if (monitoringIntervalRef.current) {
      clearInterval(monitoringIntervalRef.current);
      monitoringIntervalRef.current = null;
    }
    
    setIsMonitoring(false);
    setSessionId(null);
    sessionRef.current = null;
    console.log('Stopped window monitoring');
  };

  const formatDuration = (startTime) => {
    if (!startTime) return '00:00';
    
    const now = new Date();
    const diff = Math.floor((now - startTime) / 1000);
    const minutes = Math.floor(diff / 60);
    const seconds = diff % 60;
    
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Monitor className="h-5 w-5" />
            Real Window Monitor
          </CardTitle>
          <CardDescription>
            Monitor your actual active windows and get real-time distraction alerts
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Status and Controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${isMonitoring ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                <span className="text-sm">
                  {isMonitoring ? 'Monitoring Active' : 'Not Monitoring'}
                </span>
              </div>
              
              {isMonitoring && monitoringStats.startTime && (
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Clock className="h-4 w-4" />
                  {formatDuration(monitoringStats.startTime)}
                </div>
              )}
            </div>
            
            <div className="flex gap-2">
              {!isMonitoring ? (
                <Button 
                  onClick={startMonitoring}
                  disabled={!isBackendAvailable}
                  className="flex items-center gap-2"
                >
                  <Play className="h-4 w-4" />
                  Start Monitoring
                </Button>
              ) : (
                <Button 
                  onClick={stopMonitoring}
                  variant="destructive"
                  className="flex items-center gap-2"
                >
                  <Stop className="h-4 w-4" />
                  Stop Monitoring
                </Button>
              )}
            </div>
          </div>

          {/* Current Window Display */}
          <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <h4 className="font-medium mb-2">Current Active Window</h4>
            <div className="font-mono text-sm break-all">
              {currentWindow}
            </div>
          </div>

          {/* Monitoring Stats */}
          {isMonitoring && (
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{monitoringStats.windowChanges}</div>
                <div className="text-sm text-blue-600">Window Changes</div>
              </div>
              <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                <div className="text-2xl font-bold text-red-600">{monitoringStats.distractions}</div>
                <div className="text-sm text-red-600">Distractions</div>
              </div>
              <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{monitoringStats.productive}</div>
                <div className="text-sm text-green-600">Productive</div>
              </div>
            </div>
          )}

          {/* Last Activity */}
          {lastActivity && (
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <h4 className="font-medium mb-2">Last Activity</h4>
              <div className="flex items-center gap-3">
                {lastActivity.isDistraction ? (
                  <AlertTriangle className="h-5 w-5 text-red-500" />
                ) : (
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                )}
                <div className="flex-1">
                  <div className="font-medium">{lastActivity.windowTitle}</div>
                  <div className="text-sm text-gray-600">
                    {lastActivity.classification} (confidence: {lastActivity.confidence.toFixed(2)})
                  </div>
                </div>
                <Badge variant={lastActivity.isDistraction ? "destructive" : "default"}>
                  {lastActivity.isDistraction ? "Distraction" : "Productive"}
                </Badge>
              </div>
            </div>
          )}

          {/* Activity History */}
          {activityHistory.length > 0 && (
            <div>
              <h4 className="font-medium mb-2">Recent Activity</h4>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {activityHistory.map((activity, index) => (
                  <div key={index} className="flex items-center gap-3 p-2 bg-gray-50 dark:bg-gray-800 rounded text-sm">
                    {activity.isDistraction ? (
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                    ) : (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="truncate">{activity.windowTitle}</div>
                      <div className="text-xs text-gray-500">
                        {activity.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {activity.classification}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Important Note */}
          <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-yellow-800 dark:text-yellow-200">Important Note</h4>
                <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                  This component currently simulates window monitoring. To get real window data, you need to:
                  <br />• Run the Python backend with the new <code>window_monitor.py</code>
                  <br />• Install required dependencies: <code>pip install pywin32 psutil</code>
                  <br />• The backend will handle real window monitoring and send notifications
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default RealWindowMonitor;
