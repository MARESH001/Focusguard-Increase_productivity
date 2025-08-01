import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  ArrowLeft, 
  TrendingUp, 
  Clock, 
  Target, 
  AlertTriangle,
  Calendar,
  BarChart3,
  Flame,
  Zap
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, AreaChart, Area } from 'recharts';

const Statistics = ({ user, apiBaseUrl }) => {
  const navigate = useNavigate();
  const [weeklyStats, setWeeklyStats] = useState({});
  const [progressData, setProgressData] = useState({});
  const [recentSessions, setRecentSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState('week');

  useEffect(() => {
    fetchStatistics();
  }, [user]);

  const fetchStatistics = async () => {
    try {
      // Fetch weekly stats
      const weeklyResponse = await fetch(`${apiBaseUrl}/users/${user.username}/stats/weekly`);
      if (weeklyResponse.ok) {
        const weekly = await weeklyResponse.json();
        setWeeklyStats(weekly);
      }

      // Fetch progress data
      const progressResponse = await fetch(`${apiBaseUrl}/users/${user.username}/progress/`);
      if (progressResponse.ok) {
        const progress = await progressResponse.json();
        setProgressData(progress);
      }

      // Fetch recent sessions
      const sessionsResponse = await fetch(`${apiBaseUrl}/users/${user.username}/sessions/`);
      if (sessionsResponse.ok) {
        const sessions = await sessionsResponse.json();
        setRecentSessions(sessions);
      }
    } catch (error) {
      console.error('Error fetching statistics:', error);
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

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const getWeeklyChartData = () => {
    return Object.entries(weeklyStats).map(([date, stats]) => ({
      date: formatDate(date),
      focusTime: stats.total_focus_time,
      sessions: stats.completed_sessions,
      distractions: stats.total_distractions
    })).reverse();
  };

  const getProgressChartData = () => {
    if (!progressData.progress_data) return [];
    
    return progressData.progress_data.map((day) => ({
      date: formatDate(day.date),
      focusTime: day.focus_time_minutes,
      productivity: Math.round(day.productivity_score * 100),
      distractions: day.distraction_count,
      streak: day.streak_days,
      isBreak: day.is_break
    }));
  };

  const getTotalStats = () => {
    const totalSessions = Object.values(weeklyStats).reduce((sum, day) => sum + day.total_sessions, 0);
    const completedSessions = Object.values(weeklyStats).reduce((sum, day) => sum + day.completed_sessions, 0);
    const totalFocusTime = Object.values(weeklyStats).reduce((sum, day) => sum + day.total_focus_time, 0);
    const totalDistractions = Object.values(weeklyStats).reduce((sum, day) => sum + day.total_distractions, 0);
    
    return {
      totalSessions,
      completedSessions,
      totalFocusTime,
      totalDistractions,
      completionRate: totalSessions > 0 ? (completedSessions / totalSessions) * 100 : 0,
      avgDistractions: totalSessions > 0 ? totalDistractions / totalSessions : 0
    };
  };

  const getProductivityTrend = () => {
    const chartData = getWeeklyChartData();
    if (chartData.length < 2) return 'stable';
    
    const recent = chartData.slice(-3);
    const earlier = chartData.slice(0, -3);
    
    const recentAvg = recent.reduce((sum, day) => sum + day.focusTime, 0) / recent.length;
    const earlierAvg = earlier.length > 0 ? earlier.reduce((sum, day) => sum + day.focusTime, 0) / earlier.length : recentAvg;
    
    if (recentAvg > earlierAvg * 1.1) return 'improving';
    if (recentAvg < earlierAvg * 0.9) return 'declining';
    return 'stable';
  };

  const getStreakStatus = () => {
    const currentStreak = progressData.current_streak || 0;
    const longestStreak = progressData.longest_streak || 0;
    
    if (currentStreak === 0) return 'broken';
    if (currentStreak >= longestStreak) return 'record';
    if (currentStreak >= 7) return 'strong';
    if (currentStreak >= 3) return 'building';
    return 'starting';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading statistics...</p>
        </div>
      </div>
    );
  }

  const totalStats = getTotalStats();
  const chartData = getWeeklyChartData();
  const progressChartData = getProgressChartData();
  const productivityTrend = getProductivityTrend();
  const streakStatus = getStreakStatus();

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Button variant="outline" onClick={() => navigate('/')} className="hover-glow">
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Statistics & Analytics</h1>
            <p className="text-muted-foreground">Track your focus and productivity over time</p>
          </div>
        </div>

        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Card className="hover-glow">
            <CardContent className="pt-6">
              <div className="text-center">
                <Clock className="h-8 w-8 mx-auto mb-2 text-blue-400" />
                <div className="text-2xl font-bold">{formatTime(totalStats.totalFocusTime)}</div>
                <div className="text-sm text-muted-foreground">Total Focus Time</div>
              </div>
            </CardContent>
          </Card>

          <Card className="hover-glow">
            <CardContent className="pt-6">
              <div className="text-center">
                <Target className="h-8 w-8 mx-auto mb-2 text-green-400" />
                <div className="text-2xl font-bold">{totalStats.completedSessions}</div>
                <div className="text-sm text-muted-foreground">Completed Sessions</div>
              </div>
            </CardContent>
          </Card>

          <Card className="hover-glow">
            <CardContent className="pt-6">
              <div className="text-center">
                <TrendingUp className="h-8 w-8 mx-auto mb-2 text-purple-400" />
                <div className="text-2xl font-bold">{Math.round(totalStats.completionRate)}%</div>
                <div className="text-sm text-muted-foreground">Completion Rate</div>
              </div>
            </CardContent>
          </Card>

          <Card className="hover-glow">
            <CardContent className="pt-6">
              <div className="text-center">
                <AlertTriangle className="h-8 w-8 mx-auto mb-2 text-yellow-400" />
                <div className="text-2xl font-bold">{Math.round(totalStats.avgDistractions * 10) / 10}</div>
                <div className="text-sm text-muted-foreground">Avg Distractions</div>
              </div>
            </CardContent>
          </Card>

          <Card className="hover-glow">
            <CardContent className="pt-6">
              <div className="text-center">
                <Flame className="h-8 w-8 mx-auto mb-2 text-orange-400" />
                <div className="text-2xl font-bold">{progressData.current_streak || 0}</div>
                <div className="text-sm text-muted-foreground">Current Streak</div>
                <div className="text-xs text-muted-foreground mt-1">
                  Best: {progressData.longest_streak || 0}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Streak Status */}
        <Card className="hover-glow">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Flame className="h-5 w-5" />
              Focus Streak
            </CardTitle>
            <CardDescription>
              Your consecutive days of focus activity
              <Badge 
                className={`ml-2 ${
                  streakStatus === 'record' ? 'bg-orange-600' :
                  streakStatus === 'strong' ? 'bg-green-600' :
                  streakStatus === 'building' ? 'bg-blue-600' :
                  streakStatus === 'starting' ? 'bg-yellow-600' : 'bg-red-600'
                }`}
              >
                {streakStatus === 'record' ? '🔥 New Record!' :
                 streakStatus === 'strong' ? '🔥 Strong Streak' :
                 streakStatus === 'building' ? '🔥 Building' :
                 streakStatus === 'starting' ? '🔥 Starting' : '💔 Broken'}
              </Badge>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold mb-2">Current Streak: {progressData.current_streak || 0} days</h4>
                <p className="text-sm text-muted-foreground mb-4">
                  {progressData.current_streak === 0 ? 
                    "Start a focus session today to begin your streak!" :
                    `Keep going! You're on fire with ${progressData.current_streak} consecutive days.`
                  }
                </p>
                {progressData.current_streak > 0 && (
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-yellow-500" />
                    <span className="text-sm">
                      {progressData.current_streak >= progressData.longest_streak ? 
                        "You're setting a new record!" :
                        `${progressData.longest_streak - progressData.current_streak} more days to beat your record`
                      }
                    </span>
                  </div>
                )}
              </div>
              <div>
                <h4 className="font-semibold mb-2">Streak History</h4>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Longest Streak:</span>
                    <span className="font-medium">{progressData.longest_streak || 0} days</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Total Focus Time:</span>
                    <span className="font-medium">{formatTime(progressData.total_focus_time || 0)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Average Productivity:</span>
                    <span className="font-medium">{Math.round((progressData.average_productivity || 0) * 100)}%</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Progress Graph */}
        <Card className="hover-glow">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Progress & Streak Tracking
            </CardTitle>
            <CardDescription>
              Your focus time and productivity over time. Breaks in the graph indicate days without focus sessions.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {progressChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={progressChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
                  <XAxis 
                    dataKey="date" 
                    stroke="#a0a0a0"
                    fontSize={12}
                  />
                  <YAxis 
                    stroke="#a0a0a0"
                    fontSize={12}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: '#3c3c3c',
                      border: '1px solid #505050',
                      borderRadius: '8px',
                      color: '#ffffff'
                    }}
                    formatter={(value, name) => [
                      name === 'focusTime' ? formatTime(value) : 
                      name === 'productivity' ? `${value}%` : value,
                      name === 'focusTime' ? 'Focus Time' : 
                      name === 'productivity' ? 'Productivity' : 
                      name === 'distractions' ? 'Distractions' : 'Streak'
                    ]}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="focusTime" 
                    stroke="#ffffff" 
                    fill="#ffffff"
                    fillOpacity={0.3}
                    strokeWidth={2}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="productivity" 
                    stroke="#10b981" 
                    strokeWidth={2}
                    dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No progress data available yet. Complete some focus sessions to see your trends!</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Productivity Trend */}
        <Card className="hover-glow">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Weekly Focus Trend
            </CardTitle>
            <CardDescription>
              Your focus time over the past week
              <Badge 
                className={`ml-2 ${
                  productivityTrend === 'improving' ? 'bg-green-600' :
                  productivityTrend === 'declining' ? 'bg-red-600' : 'bg-gray-600'
                }`}
              >
                {productivityTrend === 'improving' ? '📈 Improving' :
                 productivityTrend === 'declining' ? '📉 Declining' : '➡️ Stable'}
              </Badge>
            </CardDescription>
          </CardHeader>
          <CardContent>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
                  <XAxis 
                    dataKey="date" 
                    stroke="#a0a0a0"
                    fontSize={12}
                  />
                  <YAxis 
                    stroke="#a0a0a0"
                    fontSize={12}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: '#3c3c3c',
                      border: '1px solid #505050',
                      borderRadius: '8px',
                      color: '#ffffff'
                    }}
                    formatter={(value, name) => [
                      name === 'focusTime' ? formatTime(value) : value,
                      name === 'focusTime' ? 'Focus Time' : 
                      name === 'sessions' ? 'Sessions' : 'Distractions'
                    ]}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="focusTime" 
                    stroke="#ffffff" 
                    strokeWidth={2}
                    dot={{ fill: '#ffffff', strokeWidth: 2, r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No data available yet. Complete some focus sessions to see your trends!</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Daily Breakdown */}
        <Card className="hover-glow">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Daily Breakdown
            </CardTitle>
            <CardDescription>
              Sessions and distractions by day
            </CardDescription>
          </CardHeader>
          <CardContent>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
                  <XAxis 
                    dataKey="date" 
                    stroke="#a0a0a0"
                    fontSize={12}
                  />
                  <YAxis 
                    stroke="#a0a0a0"
                    fontSize={12}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: '#3c3c3c',
                      border: '1px solid #505050',
                      borderRadius: '8px',
                      color: '#ffffff'
                    }}
                  />
                  <Bar dataKey="sessions" fill="#ffffff" name="Sessions" />
                  <Bar dataKey="distractions" fill="#ef4444" name="Distractions" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No daily data available yet.</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Sessions */}
        <Card className="hover-glow">
          <CardHeader>
            <CardTitle>Recent Sessions</CardTitle>
            <CardDescription>
              Your latest focus sessions and their performance
            </CardDescription>
          </CardHeader>
          <CardContent>
            {recentSessions.length > 0 ? (
              <div className="space-y-4">
                {recentSessions.slice(0, 10).map((session) => (
                  <div key={session.id} className="flex items-center justify-between p-4 rounded-lg bg-card border">
                    <div className="flex-1">
                      <h4 className="font-medium">{session.task_description}</h4>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                        <span>{formatTime(session.duration_minutes)}</span>
                        <span>•</span>
                        <span>{session.distraction_count} distractions</span>
                        <span>•</span>
                        <span>{new Date(session.start_time).toLocaleDateString()}</span>
                      </div>
                      {session.keywords && session.keywords.length > 0 && (
                        <div className="flex gap-1 mt-2">
                          {session.keywords.slice(0, 3).map((keyword, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              {keyword}
                            </Badge>
                          ))}
                          {session.keywords.length > 3 && (
                            <Badge variant="outline" className="text-xs">
                              +{session.keywords.length - 3}
                            </Badge>
                          )}
                        </div>
                      )}
                    </div>
                    <div className="text-right">
                      <Badge 
                        className={session.completed ? 'bg-green-600' : 'bg-yellow-600'}
                      >
                        {session.completed ? 'Completed' : 'Incomplete'}
                      </Badge>
                      <div className="text-sm text-muted-foreground mt-1">
                        {Math.round(session.productivity_score * 100)}% productive
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No sessions yet. Start your first focus session to see statistics!</p>
                <Button 
                  className="mt-4"
                  onClick={() => navigate('/timer')}
                >
                  Start Focus Session
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Insights */}
        <Card className="hover-glow">
          <CardHeader>
            <CardTitle>💡 Insights & Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <h4 className="font-semibold">📊 Your Performance</h4>
                <ul className="space-y-1 text-muted-foreground">
                  <li>• Average session length: {totalStats.totalSessions > 0 ? formatTime(Math.round(totalStats.totalFocusTime / totalStats.completedSessions)) : 'N/A'}</li>
                  <li>• Best completion rate: {Math.round(totalStats.completionRate)}%</li>
                  <li>• Distraction frequency: {Math.round(totalStats.avgDistractions * 10) / 10} per session</li>
                  <li>• Current streak: {progressData.current_streak || 0} days</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h4 className="font-semibold">🎯 Recommendations</h4>
                <ul className="space-y-1 text-muted-foreground">
                  {totalStats.avgDistractions > 3 && (
                    <li>• Try shorter sessions to reduce distractions</li>
                  )}
                  {totalStats.completionRate < 70 && (
                    <li>• Set more realistic session durations</li>
                  )}
                  {totalStats.totalSessions < 5 && (
                    <li>• Build consistency with daily focus sessions</li>
                  )}
                  {(progressData.current_streak || 0) === 0 && (
                    <li>• Start a focus session today to begin your streak</li>
                  )}
                  <li>• Use specific keywords for better AI detection</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Statistics;

