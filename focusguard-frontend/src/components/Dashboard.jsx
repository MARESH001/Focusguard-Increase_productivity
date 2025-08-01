import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  Timer, 
  BarChart3, 
  Calendar, 
  LogOut, 
  Play, 
  Target,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import NotificationCenter from './NotificationCenter';

const Dashboard = ({ user, onLogout, apiBaseUrl }) => {
  const navigate = useNavigate();
  const [todayStats, setTodayStats] = useState(null);
  const [recentSessions, setRecentSessions] = useState([]);
  const [todayPlan, setTodayPlan] = useState(null);
  const [timeSpentPerApp, setTimeSpentPerApp] = useState({});
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, [user]);

  const fetchDashboardData = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      
      // Fetch today's stats
      const statsResponse = await fetch(`${apiBaseUrl}/users/${user.username}/stats/${today}`);
      if (statsResponse.ok) {
        const stats = await statsResponse.json();
        setTodayStats(stats);
      }

      // Fetch recent sessions
      const sessionsResponse = await fetch(`${apiBaseUrl}/users/${user.username}/sessions/`);
      if (sessionsResponse.ok) {
        const sessions = await sessionsResponse.json();
        setRecentSessions(sessions.slice(0, 5)); // Get last 5 sessions
      }

      // Fetch today's plan
      const planResponse = await fetch(`${apiBaseUrl}/users/${user.username}/plans/${today}`);
      if (planResponse.ok) {
        const plan = await planResponse.json();
        setTodayPlan(plan);
      }

      // ✅ Now safely fetch time spent per app
      const timeSpentResponse = await fetch(`${apiBaseUrl}/users/${user.username}/activity/time_spent?start_date=${today}&end_date=${today}`);
      if (timeSpentResponse.ok) {
        const timeSpent = await timeSpentResponse.json();
        setTimeSpentPerApp(timeSpent);
      }

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (minutes) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  const getProductivityColor = (score) => {
    if (score >= 0.8) return 'text-green-400';
    if (score >= 0.6) return 'text-yellow-400';
    return 'text-red-400';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Welcome back, {user.username}</h1>
            <p className="text-muted-foreground">
              Ready to focus and be productive today?
            </p>
          </div>
          <div className="flex items-center gap-4">
            <NotificationCenter user={user} apiBaseUrl={apiBaseUrl} />
            <Button variant="outline" onClick={onLogout} className="hover-glow">
              <LogOut className="h-4 w-4 mr-2" />
              Sign Out
            </Button>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Button 
            onClick={() => navigate('/timer')}
            className="h-20 hover-glow flex flex-col gap-2"
            size="lg"
          >
            <Play className="h-6 w-6" />
            Start Focus Session
          </Button>
          
          <Button 
            variant="outline"
            onClick={() => navigate('/plan')}
            className="h-20 hover-glow flex flex-col gap-2"
          >
            <Calendar className="h-6 w-6" />
            Daily Plan
          </Button>
          
          <Button 
            variant="outline"
            onClick={() => navigate('/stats')}
            className="h-20 hover-glow flex flex-col gap-2"
          >
            <BarChart3 className="h-6 w-6" />
            Statistics
          </Button>
          
          <Button 
            variant="outline"
            className="h-20 hover-glow flex flex-col gap-2"
            disabled
          >
            <Target className="h-6 w-6" />
            Goals (Soon)
          </Button>
        </div>

        {/* Today's Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Today's Stats */}
          <Card className="hover-glow">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Today's Progress
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {todayStats ? (
                <>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Sessions</span>
                    <Badge variant="secondary">
                      {todayStats.completed_sessions}/{todayStats.total_sessions}
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Focus Time</span>
                    <span className="font-semibold">
                      {formatTime(todayStats.total_focus_time)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Productivity</span>
                    <span className={`font-semibold ${getProductivityColor(todayStats.average_productivity)}`}>
                      {Math.round(todayStats.average_productivity * 100)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Distractions</span>
                    <Badge variant={todayStats.total_distractions > 5 ? "destructive" : "secondary"}>
                      {todayStats.total_distractions}
                    </Badge>
                  </div>
                </>
              ) : (
                <p className="text-muted-foreground text-center py-4">
                  No sessions today yet. Start your first focus session!
                </p>
              )}
            </CardContent>
          </Card>

          {/* Today's Plan */}
          <Card className="hover-glow">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Today's Plan
              </CardTitle>
            </CardHeader>
            <CardContent>
              {todayPlan ? (
                <div className="space-y-3">
                  <p className="text-sm">{todayPlan.plan_text}</p>
                  <div className="flex items-center gap-2">
                    {todayPlan.completed ? (
                      <Badge className="bg-green-600">
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                        Completed
                      </Badge>
                    ) : (
                      <Badge variant="outline">
                        <Clock className="h-3 w-3 mr-1" />
                        In Progress
                      </Badge>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-muted-foreground mb-3">No plan set for today</p>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => navigate('/plan')}
                  >
                    Create Plan
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card className="hover-glow">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Timer className="h-5 w-5" />
                Recent Sessions
              </CardTitle>
            </CardHeader>
            <CardContent>
              {recentSessions.length > 0 ? (
                <div className="space-y-3">
                  {recentSessions.map((session) => (
                    <div key={session.id} className="flex items-center justify-between text-sm">
                      <div className="flex-1">
                        <p className="font-medium truncate">
                          {session.task_description}
                        </p>
                        <p className="text-muted-foreground text-xs">
                          {formatTime(session.duration_minutes)} • 
                          {session.distraction_count} distractions
                        </p>
                      </div>
                      <div className="flex items-center gap-1">
                        {session.completed ? (
                          <CheckCircle2 className="h-4 w-4 text-green-400" />
                        ) : (
                          <AlertTriangle className="h-4 w-4 text-yellow-400" />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-center py-4">
                  No sessions yet. Start your first focus session!
                </p>
              )}
            </CardContent>
          </Card>

          {/* Time Spent Per App */}
          <Card className="hover-glow">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Time Spent Per App
              </CardTitle>
            </CardHeader>
            <CardContent>
              {Object.keys(timeSpentPerApp).length > 0 ? (
                <div className="space-y-3">
                  {Object.entries(timeSpentPerApp).map(([app, time]) => (
                    <div key={app} className="flex items-center justify-between text-sm">
                      <p className="font-medium truncate">{app}</p>
                      <p className="text-muted-foreground">
                        {formatTime(Math.round(time / 60))} {/* Convert seconds to minutes */}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-center py-4">
                  No app activity recorded yet.
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Quick Tips */}
        <Card className="hover-glow">
          <CardHeader>
            <CardTitle>💡 Focus Tips</CardTitle>
            <CardDescription>
              Maximize your productivity with these AI-powered insights
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <h4 className="font-semibold">🎯 Before Starting</h4>
                <ul className="space-y-1 text-muted-foreground">
                  <li>• Set clear, specific goals for your session</li>
                  <li>• Choose a realistic time duration (25-50 minutes)</li>
                  <li>• Eliminate potential distractions beforehand</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h4 className="font-semibold">🤖 AI Detection</h4>
                <ul className="space-y-1 text-muted-foreground">
                  <li>• FocusGuard monitors your active windows</li>
                  <li>• AI classifies content as productive or distracting</li>
                  <li>• Get gentle nudges to stay on track</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;