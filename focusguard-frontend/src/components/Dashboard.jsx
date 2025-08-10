import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Checkbox } from './ui/checkbox';
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
  AlertTriangle,
  MessageSquare
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import NotificationCenter from './NotificationCenter';
import FeedbackForm from './FeedbackForm';

const Dashboard = ({ user, onLogout, apiBaseUrl, isBackendAvailable, onBackendStatusChange }) => {
  const navigate = useNavigate();
  const [todayStats, setTodayStats] = useState(null);
  const [recentSessions, setRecentSessions] = useState([]);
  const [todayPlan, setTodayPlan] = useState(null);
  const [timeSpentPerApp, setTimeSpentPerApp] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [todayTasks, setTodayTasks] = useState([]);
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, [user]);

  const fetchCurrentDistractionCount = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/users/${user.username}/distraction-status`);
      if (response.ok) {
        const data = await response.json();
        setCurrentDistractionCount(data.current_distraction_count || 0);
      }
    } catch (error) {
      console.error('Error fetching current distraction count:', error);
    }
  };

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
      const planResponse = await fetch(`${apiBaseUrl}/users/${user.username}/plans/enhanced/${today}`);
      if (planResponse.ok) {
        const plan = await planResponse.json();
        setTodayPlan(plan);
        setTodayTasks(plan.tasks || []);
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

  const toggleTaskCompletion = async (taskId) => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await fetch(`${apiBaseUrl}/users/${user.username}/plans/enhanced/${today}/tasks/${taskId}/toggle`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        // Update local state
        setTodayTasks(prevTasks => 
          prevTasks.map(task => 
            task.id === taskId 
              ? { ...task, completed: !task.completed }
              : task
          )
        );
      }
    } catch (error) {
      console.error('Error toggling task completion:', error);
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
            {!isBackendAvailable && (
              <div className="flex items-center gap-2 mt-2 p-2 bg-orange-100 dark:bg-orange-900/20 border border-orange-300 dark:border-orange-700 rounded-md">
                <AlertTriangle className="h-4 w-4 text-orange-600" />
                <span className="text-sm text-orange-800 dark:text-orange-200">
                  Backend connection lost. Notifications and real-time features are disabled.
                </span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-4">
            
            <NotificationCenter 
              user={user} 
              apiBaseUrl={apiBaseUrl} 
              isBackendAvailable={isBackendAvailable}
              onBackendStatusChange={onBackendStatusChange}
              filterType="today-reminders"
            />
            
            {/* Feedback Button */}
            <div className="relative">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowFeedbackForm(true)}
                className="flex items-center gap-2 hover:bg-blue-50 hover:border-blue-300"
                title="Submit Feedback"
              >
                <MessageSquare className="h-4 w-4" />
                <span className="hidden sm:inline">Feedback</span>
              </Button>
            </div>
            
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
                </>
              ) : (
                <p className="text-muted-foreground text-center py-4">
                  No sessions today yet. Start your first focus session!
                </p>
              )}
            </CardContent>
          </Card>

          {/* Today's Tasks */}
          <Card className="hover-glow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Today's Tasks
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={fetchDashboardData}
                  className="h-6 w-6 p-0"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {todayTasks.length > 0 ? (
                <div className="space-y-3">
                  {todayTasks.map((task) => (
                    <div key={task.id} className="flex items-center gap-3">
                      <Checkbox
                        checked={task.completed}
                        onCheckedChange={() => toggleTaskCompletion(task.id)}
                        className="flex-shrink-0"
                      />
                      <span 
                        className={`flex-1 text-sm ${
                          task.completed 
                            ? 'line-through text-red-500' 
                            : 'text-white'
                        }`}
                      >
                        {task.text}
                      </span>
                    </div>
                  ))}
                  <div className="pt-2 border-t">
                    <div className="flex justify-between items-center text-xs text-muted-foreground">
                      <span>Progress</span>
                      <span>
                        {todayTasks.filter(t => t.completed).length} / {todayTasks.length}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1 mt-1">
                      <div 
                        className="bg-green-500 h-1 rounded-full transition-all duration-300"
                        style={{ 
                          width: `${todayTasks.length > 0 
                            ? (todayTasks.filter(t => t.completed).length / todayTasks.length) * 100 
                            : 0}%` 
                        }}
                      ></div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-muted-foreground mb-3">No tasks for today</p>
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

      {/* Feedback Components */}
      <FeedbackForm
        isOpen={showFeedbackForm}
        onClose={() => setShowFeedbackForm(false)}
        username={user.username}
        apiBaseUrl={apiBaseUrl}
      />
      
    </div>
  );
};

export default Dashboard;