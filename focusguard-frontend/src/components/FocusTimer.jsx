import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { 
  ArrowLeft, 
  Play, 
  Pause, 
  Square, 
  Timer, 
  Target,
  AlertTriangle,
  CheckCircle2,
  Volume2,
  VolumeX
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const FocusTimer = ({ user, apiBaseUrl }) => {
  const navigate = useNavigate();
  const [isSetup, setIsSetup] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [timeLeft, setTimeLeft] = useState(25 * 60); // 25 minutes in seconds
  const [totalTime, setTotalTime] = useState(25 * 60);
  const [currentSession, setCurrentSession] = useState(null);
  const [distractionCount, setDistractionCount] = useState(0);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [keywords, setKeywords] = useState("");
  const [duration, setDuration] = useState(25);
  const [taskDescription, setTaskDescription] = useState("");
  const [customSound, setCustomSound] = useState(null);
  const [notificationPermission, setNotificationPermission] = useState("default");

  const intervalRef = useRef(null);
  const activityLogIntervalRef = useRef(null);
  const audioRef = useRef(null);
  const distractionCountIntervalRef = useRef(null);

  useEffect(() => {
    // Initialize audio for notifications
    audioRef.current = new Audio();
    
    // Request notification permission
    requestNotificationPermission();
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (distractionCountIntervalRef.current) {
        clearInterval(distractionCountIntervalRef.current);
      }
    };
  }, []);

  // Fetch real-time distraction count when session is active
  useEffect(() => {
    if (currentSession && isRunning) {
      // Fetch initial distraction count
      fetchDistractionCount();
      
      // Set up interval to fetch distraction count every 5 seconds
      distractionCountIntervalRef.current = setInterval(() => {
        fetchDistractionCount();
      }, 5000);
      
      return () => {
        if (distractionCountIntervalRef.current) {
          clearInterval(distractionCountIntervalRef.current);
        }
      };
    }
  }, [currentSession, isRunning]);

  const fetchDistractionCount = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/users/${user.username}/distraction-status`);
      if (response.ok) {
        const data = await response.json();
        setDistractionCount(data.current_distraction_count || 0);
        console.log('📊 Updated distraction count:', data.current_distraction_count);
      }
    } catch (error) {
      console.error('Error fetching distraction count:', error);
    }
  };

  useEffect(() => {
    if (isRunning && !isPaused && timeLeft > 0) {
      intervalRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            handleSessionComplete();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isRunning, isPaused, timeLeft]);

  useEffect(() => {
    const savedSession = localStorage.getItem('focusguard_current_session');
    if (savedSession && !currentSession) {
      const sessionObj = JSON.parse(savedSession);
      setCurrentSession(sessionObj);
      setIsSetup(true);
      setIsRunning(true);
      // Optionally restore timeLeft, distractionCount, etc. if you store them
    }
  }, []);

  const requestNotificationPermission = async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      setNotificationPermission(permission);
    }
  };

  const handleCustomSoundUpload = (event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith('audio/')) {
      const url = URL.createObjectURL(file);
      setCustomSound(url);
    }
  };



  const handleStartSession = async () => {
    try {
      const keywordList = keywords.split(",").map(k => k.trim()).filter(k => k);
      const response = await fetch(`${apiBaseUrl}/users/${user.username}/sessions/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          task_description: taskDescription.trim() || "Focused session",
          keywords: keywordList,
          duration_minutes: duration
        }),
      });

      if (response.ok) {
        const session = await response.json();
        setCurrentSession(session);
        setTotalTime(duration * 60);
        setTimeLeft(duration * 60);
        setIsSetup(true);
        setIsRunning(true);
        setDistractionCount(0);
        // Store session in localStorage for resuming
        localStorage.setItem('focusguard_current_session', JSON.stringify(session));
        // Start monitoring (in a real app, this would communicate with a background service)
        startMonitoring(session.id);
      }
    } catch (error) {
      console.error('Error starting session:', error);
      alert('Failed to start session. Please try again.');
    }
  };

  const startMonitoring = (sessionId) => {
    // Real window monitoring is handled by the backend window_monitor.py
    // This function only starts the timer, not window monitoring
    console.log("Timer started - real window monitoring handled by backend");
    
    // Clear any existing monitoring
    if (activityLogIntervalRef.current) {
      clearInterval(activityLogIntervalRef.current);
      activityLogIntervalRef.current = null;
    }
  };

  // NOTE: Ensure your monitoring logic always calls handleDistraction(currentSession.id) for every distraction event, not just the first one.

  const stopMonitoring = () => {
    if (activityLogIntervalRef.current) {
      clearInterval(activityLogIntervalRef.current);
      activityLogIntervalRef.current = null;
    }
    // Also clear the main timer interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const handleDistraction = async (sessionId) => {
    setDistractionCount(prev => prev + 1);
    
    // Play notification sound and send desktop notification
    playNotificationSound();
    
    sendDesktopNotification(
      "Focus Alert! 🚨", 
      "You seem to be getting distracted. Stay focused on your task!"
    );

    // Note: Real window monitoring is handled by the backend window_monitor.py
    // This function only handles the timer-based distraction count
    console.log("Distraction detected - real window monitoring handled by backend");
  };

  const playNotificationSound = () => {
    if (soundEnabled) {
      if (customSound) {
        // Use custom uploaded sound
        const audio = new Audio(customSound);
        audio.play().catch(error => {
          console.error('Error playing custom sound:', error);
          playDefaultSound();
        });
      } else {
        // Use default sound
        playDefaultSound();
      }
    }
  };

  const playDefaultSound = () => {
    // Create a simple beep sound
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = 800;
    oscillator.type = 'sine';
    
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
  };

  const sendDesktopNotification = async (title, message) => {
    if (!('Notification' in window)) return;
    if (Notification.permission !== 'granted') {
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') return;
    }
    new Notification(title, {
      body: message,
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      tag: 'focusguard-notification',
      requireInteraction: false,
      silent: false
    });
  };

  const handlePause = () => {
    setIsPaused(!isPaused);
  };

  const handleStop = async () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (activityLogIntervalRef.current) {
      clearInterval(activityLogIntervalRef.current);
      activityLogIntervalRef.current = null;
    }
    if (currentSession) {
      await updateSession(false);
    }
    // Optionally remove session from localStorage if you store it
    localStorage.removeItem('focusguard_current_session');
    resetTimer();
  };

  const handleSessionComplete = async () => {
    if (currentSession) {
      await updateSession(true);
    }
    
    // Play completion sound and send desktop notification
    if (soundEnabled) {
      playCompletionSound();
    }
    sendDesktopNotification(
      "Session Complete! 🎉", 
      "Great job! Your focus session has been completed successfully."
    );
    
    resetTimer();
  };

  const updateSession = async (completed) => {
    try {
      const productivityScore = Math.max(0, 1 - (distractionCount * 0.1));
      await fetch(`${apiBaseUrl}/sessions/${currentSession.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          completed,
          distraction_count: distractionCount,
          productivity_score: productivityScore,
          end_time: new Date().toISOString()
        }),
      });
    } catch (error) {
      console.error('Error updating session:', error);
    }
  };

  const playCompletionSound = () => {
    // Play a pleasant completion melody
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const notes = [523.25, 659.25, 783.99]; // C, E, G
    
    notes.forEach((freq, index) => {
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.value = freq;
      oscillator.type = 'sine';
      
      const startTime = audioContext.currentTime + (index * 0.2);
      gainNode.gain.setValueAtTime(0.2, startTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + 0.3);
      
      oscillator.start(startTime);
      oscillator.stop(startTime + 0.3);
    });
  };

  const resetTimer = () => {
    setIsRunning(false);
    setIsPaused(false);
    setIsSetup(false);
    setCurrentSession(null);
    setDistractionCount(0);
    
    // Clear monitoring
    stopMonitoring();
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getProgressPercentage = () => {
    return ((totalTime - timeLeft) / totalTime) * 100;
  };

  if (!isSetup) {
    return (
      <div className="min-h-screen p-4">
        <div className="max-w-2xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex items-center gap-4">
            <Button variant="outline" onClick={() => navigate('/')} className="hover-glow">
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold">Start Focus Session</h1>
              <p className="text-muted-foreground">Set up your focused work session</p>
            </div>
          </div>

          {/* Setup Form */}
          <Card className="hover-glow">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Session Setup
              </CardTitle>
              <CardDescription>
                Configure your focus session for maximum productivity
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">




              {/* Keywords */}
              <div className="space-y-2">
                <Label htmlFor="keywords">Focus Keywords</Label>
                <Input
                  id="keywords"
                  placeholder="programming, react, javascript (comma-separated)"
                  value={keywords}
                  onChange={(e) => setKeywords(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  Keywords help AI detect if you're staying on task
                </p>
              </div>

              {/* Duration */}
              <div className="space-y-2">
                <Label htmlFor="duration">Duration (minutes)</Label>
                <Input
                  id="duration"
                  type="number"
                  min="5"
                  max="120"
                  value={duration}
                  onChange={(e) => setDuration(parseInt(e.target.value) || 25)}
                />
              </div>

              {/* Sound Settings */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="soundEnabled"
                    checked={soundEnabled}
                    onChange={(e) => setSoundEnabled(e.target.checked)}
                    className="rounded"
                  />
                  <Label htmlFor="soundEnabled" className="text-sm">
                    Enable notification sounds
                  </Label>
                </div>
                
                {/* Custom Sound Upload */}
                <div className="space-y-2">
                  <Label htmlFor="customSound" className="text-sm">
                    Custom notification sound (optional)
                  </Label>
                  <Input
                    id="customSound"
                    type="file"
                    accept="audio/*"
                    onChange={handleCustomSoundUpload}
                    className="text-sm"
                  />
                  <p className="text-xs text-muted-foreground">
                    Upload your own audio file (MP3, WAV, etc.) or leave empty for default sound
                  </p>
                  {customSound && (
                    <div className="flex items-center gap-2 text-xs text-green-600">
                      <CheckCircle2 className="h-3 w-3" />
                      Custom sound uploaded successfully
                    </div>
                  )}
                </div>
              </div>

              <Button 
                onClick={handleStartSession}
                className="w-full hover-glow"
                size="lg"
              >
                <Play className="h-5 w-5 mr-2" />
                Start Focus Session
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="outline" onClick={() => navigate('/')} className="hover-glow">
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold">Focus Session</h1>
              <p className="text-muted-foreground">{currentSession?.task_description}</p>
            </div>
          </div>
          <Button 
            variant="outline" 
            onClick={() => setSoundEnabled(!soundEnabled)}
            className="hover-glow"
          >
            {soundEnabled ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
          </Button>
        </div>

        {/* Timer Display */}
        <Card className="hover-glow">
          <CardContent className="pt-6">
            <div className="text-center space-y-6">
              {/* Circular Progress */}
              <div className="relative w-64 h-64 mx-auto">
                <svg className="w-64 h-64 transform -rotate-90" viewBox="0 0 100 100">
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    stroke="currentColor"
                    strokeWidth="2"
                    fill="none"
                    className="text-muted opacity-20"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    stroke="currentColor"
                    strokeWidth="2"
                    fill="none"
                    strokeDasharray={`${getProgressPercentage() * 2.83} 283`}
                    className="text-primary transition-all duration-1000 ease-linear"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-4xl font-bold font-mono">
                      {formatTime(timeLeft)}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {isPaused ? 'Paused' : isRunning ? 'Focusing' : 'Ready'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Controls */}
              <div className="flex items-center justify-center gap-4">
                <Button
                  onClick={handlePause}
                  variant="outline"
                  size="lg"
                  className="hover-glow"
                  disabled={!isRunning}
                >
                  {isPaused ? <Play className="h-5 w-5" /> : <Pause className="h-5 w-5" />}
                </Button>
                
                <Button
                  onClick={handleStop}
                  variant="destructive"
                  size="lg"
                  className="hover-glow"
                >
                  <Square className="h-5 w-5" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Session Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="hover-glow">
            <CardContent className="pt-6">
              <div className="text-center">
                <Timer className="h-8 w-8 mx-auto mb-2 text-primary" />
                <div className="text-2xl font-bold">{formatTime(totalTime - timeLeft)}</div>
                <div className="text-sm text-muted-foreground">Time Elapsed</div>
              </div>
            </CardContent>
          </Card>

          <Card className="hover-glow">
            <CardContent className="pt-6">
              <div className="text-center">
                <AlertTriangle className="h-8 w-8 mx-auto mb-2 text-yellow-400" />
                <div className="text-2xl font-bold flex items-center justify-center gap-2">
                  {distractionCount}
                  {isRunning && (
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" title="Live updates active"></div>
                  )}
                </div>
                <div className="text-sm text-muted-foreground">
                  Distractions {isRunning && "(Live)"}
                </div>
                {isRunning && (
                  <div className="text-xs text-green-600 mt-1">
                    📊 Real-time monitoring
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="hover-glow">
            <CardContent className="pt-6">
              <div className="text-center">
                <CheckCircle2 className="h-8 w-8 mx-auto mb-2 text-green-400" />
                <div className="text-2xl font-bold">
                  {Math.round(Math.max(0, 1 - (distractionCount * 0.1)) * 100)}%
                </div>
                <div className="text-sm text-muted-foreground">Productivity</div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Keywords */}
        {currentSession?.keywords && currentSession.keywords.length > 0 && (
          <Card className="hover-glow">
            <CardHeader>
              <CardTitle className="text-lg">Focus Keywords</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {currentSession.keywords.map((keyword, index) => (
                  <Badge key={index} variant="secondary">
                    {keyword}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tips */}
        <Card className="hover-glow">
          <CardContent className="pt-6">
            <div className="text-center text-sm text-muted-foreground">
              <p>💡 <strong>Tip:</strong> FocusGuard is monitoring your active windows and will notify you if you get distracted.</p>
              <p className="mt-2">Stay focused on your task: <strong>{currentSession?.task_description}</strong></p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default FocusTimer;
