import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  Bell, 
  X, 
  AlertTriangle, 
  Clock, 
  TrendingUp,
  Volume2,
  VolumeX,
  CheckCircle,
  Info
} from 'lucide-react';
import { toast } from 'sonner';

const NotificationCenter = ({ user, apiBaseUrl, isBackendAvailable: parentBackendAvailable, onBackendStatusChange, filterType = "all" }) => {
  const [notifications, setNotifications] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [isBackendAvailable, setIsBackendAvailable] = useState(parentBackendAvailable);
  
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  
  // Use useRef to store the latest handleNewNotification function
  const handleNewNotificationRef = useRef();
  
  // Filter notifications based on filterType
  const getFilteredNotifications = (allNotifications) => {
    if (filterType === "today-reminders") {
      const today = new Date().toISOString().split('T')[0];
      return allNotifications.filter(notification => {
        const notificationDate = new Date(notification.created_at).toISOString().split('T')[0];
        return notification.notification_type === 'reminder' && notificationDate === today;
      });
    }
    return allNotifications;
  };
  
  // Get filtered unread count
  const getFilteredUnreadCount = () => {
    const filteredNotifications = getFilteredNotifications(notifications);
    return filteredNotifications.filter(n => !n.read).length;
  };
  
  // Use useCallback to prevent stale closures
  const handleNewNotification = useCallback((notification) => {
    console.log('🔔 Processing notification:', notification);
    
    // Check if we should process this notification
    if (!isConnected && !isBackendAvailable) {
      console.log('Skipping notification - neither WebSocket connected nor backend available');
      return;
    }
    
    // Debug: Log current state values
    console.log('🔍 Notification received - State check:', {
      isConnected,
      isBackendAvailable,
      isMuted,
      notificationType: notification.notification_type
    });

    // Add to notifications list
    setNotifications(prev => [notification, ...prev]);
    setUnreadCount(prev => prev + 1);
    
    // Show toast notification
    console.log('🍞 Attempting to show toast notification...');
    if (notification.notification_type === 'distraction') {
      console.log('🚨 Showing distraction toast with message:', notification.message);
      toast.error(notification.message, {
        duration: 5000,
        action: {
          label: 'Dismiss',
          onClick: () => console.log('Toast dismissed')
        }
      });
      console.log('✅ Distraction toast called');
    } else {
      console.log('✅ Showing success toast with message:', notification.message);
      toast.success(notification.message, {
        duration: 3000
      });
      console.log('✅ Success toast called');
    }

    // Play notification sound
    console.log('🔊 Playing notification sound...');
    playNotificationSound(notification);
    
    // Show OS-level notification if permission granted
    console.log('🖥️ Attempting to show OS notification...');
    showOSNotification(notification);
    console.log('✅ OS notification attempt completed');
    
    console.log('🔔 Processing notification successfully');
  }, [isConnected, isBackendAvailable, isMuted]);

  // Store the latest handleNewNotification in the ref
  useEffect(() => {
    handleNewNotificationRef.current = handleNewNotification;
  }, [handleNewNotification]);

  // Sync with parent backend state
  useEffect(() => {
    setIsBackendAvailable(parentBackendAvailable);
  }, [parentBackendAvailable]);

  // Notify parent of backend status changes
  useEffect(() => {
    if (onBackendStatusChange) {
      onBackendStatusChange(isBackendAvailable);
    }
  }, [isBackendAvailable, onBackendStatusChange]);

  // Global audio blocker when backend is down
  useEffect(() => {
    if (!isBackendAvailable) {
      // Stop any currently playing audio
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
      
      // Clear any pending audio timeouts
      const audioElements = document.querySelectorAll('audio');
      audioElements.forEach(audio => {
        audio.pause();
        audio.currentTime = 0;
      });
      
      console.log('🔇 Audio blocked - backend unavailable');
    }
  }, [isBackendAvailable]);

  useEffect(() => {
    // Load existing notifications only if backend is available
    if (isBackendAvailable) {
      loadNotifications();
      connectWebSocket();
    }
    
    return () => {
      cleanup();
    };
  }, [user, isBackendAvailable]);

  const cleanup = () => {
    // Clear WebSocket connection
    if (wsRef.current) {
      // Clean up heartbeat interval
      if (wsRef.current.heartbeatInterval) {
        clearInterval(wsRef.current.heartbeatInterval);
        console.log('💓 Heartbeat interval cleared during cleanup');
      }
      wsRef.current.close();
      wsRef.current = null;
    }
    
    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    // Clean up audio context
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    // Reset connection state
    setIsConnected(false);
  };

  const checkBackendHealth = async () => {
    console.log('🏥 Checking backend health...');
    console.log('🔗 API Base URL:', apiBaseUrl);
    
    try {
      const response = await fetch(`${apiBaseUrl}/`, { 
        method: 'GET',
        signal: AbortSignal.timeout(3000) // 3 second timeout
      });
      
      console.log('🏥 Backend health response:', response.status, response.statusText);
      
      if (response.ok) {
        console.log('✅ Backend is healthy and available');
        setIsBackendAvailable(true);
        return true;
      } else {
        console.log('❌ Backend responded with error status:', response.status);
        setIsBackendAvailable(false);
        return false;
      }
    } catch (error) {
      console.log('❌ Backend health check failed:', error.message);
      setIsBackendAvailable(false);
      setIsConnected(false);
      return false;
    }
  };

  const loadNotifications = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/users/${user.username}/notifications/`);
      if (response.ok) {
        const data = await response.json();
        setNotifications(data);
        setUnreadCount(data.filter(n => !n.read).length);
      }
    } catch (error) {
      console.error('Error loading notifications:', error);
      setIsBackendAvailable(false);
    }
  };

  const connectWebSocket = useCallback(() => {
    if (!user?.username) {
      console.log('❌ No username available for WebSocket connection');
      return;
    }

    console.log('🔌 Attempting WebSocket connection...');
    console.log('👤 User object:', user);
    console.log('🏥 API Base URL:', apiBaseUrl);
    
    const wsUrl = `ws://${apiBaseUrl.replace('http://', '').replace('https://', '')}/ws/${user.username}`;
    console.log('🔌 WebSocket URL:', wsUrl);
    console.log('👤 Username for WebSocket:', user.username);

    const websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
      console.log('✅ WebSocket connected successfully!');
      console.log('🔌 Connection state:', websocket.readyState);
      setIsConnected(true);
      wsRef.current = websocket;
      
      // Start sending heartbeat messages to keep connection alive
      const heartbeatInterval = setInterval(() => {
        if (websocket.readyState === WebSocket.OPEN) {
          websocket.send(JSON.stringify({ type: 'heartbeat' }));
          console.log('💓 Heartbeat sent');
        } else {
          clearInterval(heartbeatInterval);
        }
      }, 30000); // Send heartbeat every 30 seconds
      
      // Store the interval reference for cleanup
      websocket.heartbeatInterval = heartbeatInterval;
    };

    websocket.onmessage = (event) => {
      console.log('📨 WebSocket message received:', event.data);
      try {
        const data = JSON.parse(event.data);
        console.log('📨 Parsed WebSocket data:', data);
        
        if (data.type === 'heartbeat_response') {
          console.log('💓 Heartbeat response received');
          return;
        }
        
        if (data.type === 'notification') {
          console.log('🔔 Notification message received, calling handleNewNotification with:', data.data);
          // Use the ref to call the latest handleNewNotification
          if (handleNewNotificationRef.current) {
            handleNewNotificationRef.current(data.data);
            console.log('✅ handleNewNotification called successfully');
          } else {
            console.log('❌ handleNewNotificationRef.current is null!');
          }
        } else {
          console.log('❓ Unknown message type:', data.type);
        }
      } catch (error) {
        console.error('❌ Error parsing WebSocket message:', error);
      }
    };

    websocket.onclose = (event) => {
      console.log('🔌 WebSocket closed:', event.code, event.reason);
      setIsConnected(false);
      wsRef.current = null;
      
      // Clear heartbeat interval
      if (websocket.heartbeatInterval) {
        clearInterval(websocket.heartbeatInterval);
      }
      
      // Attempt to reconnect after a delay
      setTimeout(() => {
        if (user?.username) {
          console.log('🔄 Attempting to reconnect WebSocket...');
          connectWebSocket();
        }
      }, 5000);
    };

    websocket.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      setIsConnected(false);
      wsRef.current = null;
      
      // Clear heartbeat interval
      if (websocket.heartbeatInterval) {
        clearInterval(websocket.heartbeatInterval);
      }
    };

    return websocket;
  }, [user?.username, apiBaseUrl]);

  const playNotificationSound = (notification) => {
    console.log('🔊 playNotificationSound ENTRY - checking conditions...');
    console.log('🔊 Connection status:', { isConnected, isMuted });
    
    if (!isConnected || isMuted) {
      console.log('🔇 Sound blocked - disconnected:', !isConnected, 'muted:', isMuted);
      return;
    }

    console.log('🔊 playNotificationSound called with:', {
      sound_type: notification.sound_type,
      custom_audio_url: notification.custom_audio_url,
      notification_type: notification.notification_type
    });

    if (notification.sound_type === 'custom' && notification.custom_audio_url) {
      console.log('🎵 Playing custom sound from URL:', notification.custom_audio_url);
      playCustomSound(notification.custom_audio_url);
    } else {
      console.log('🔊 Playing default sound (sound_type:', notification.sound_type, 'custom_audio_url:', notification.custom_audio_url, ')');
      playDefaultSound();
    }
    
    console.log('🔊 playNotificationSound EXIT');
  };

  const playDefaultSound = () => {
    console.log('🔊 playDefaultSound ENTRY');
    
    if (!isConnected || isMuted) {
      console.log('🔇 Default sound blocked - disconnected:', !isConnected, 'muted:', isMuted);
      return;
    }

    try {
      console.log('🔊 Creating audio context...');
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
        console.log('🔊 Audio context created:', audioContextRef.current.state);
      }

      console.log('🔊 Audio context state:', audioContextRef.current.state);
      
      // Handle suspended audio context (common in browsers that require user interaction)
      if (audioContextRef.current.state === 'suspended') {
        console.log('🔊 Audio context suspended, attempting to resume...');
        audioContextRef.current.resume().then(() => {
          console.log('🔊 Audio context resumed successfully');
          // Retry playing the sound after resume
          setTimeout(() => playDefaultSound(), 100);
        }).catch(error => {
          console.error('❌ Failed to resume audio context:', error);
        });
        return;
      }

      console.log('🔊 Creating oscillator and gain node...');
      const oscillator = audioContextRef.current.createOscillator();
      const gainNode = audioContextRef.current.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContextRef.current.destination);

      oscillator.frequency.setValueAtTime(800, audioContextRef.current.currentTime);
      oscillator.frequency.setValueAtTime(600, audioContextRef.current.currentTime + 0.1);

      gainNode.gain.setValueAtTime(0.3, audioContextRef.current.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContextRef.current.currentTime + 0.5);

      console.log('🔊 Starting oscillator...');
      oscillator.start(audioContextRef.current.currentTime);
      oscillator.stop(audioContextRef.current.currentTime + 0.5);

      console.log('🔊 Default notification sound played successfully');
    } catch (error) {
      console.error('❌ Error playing default sound:', error);
      console.error('❌ Error details:', {
        message: error.message,
        stack: error.stack,
        audioContextState: audioContextRef.current?.state
      });
    }
    
    console.log('🔊 playDefaultSound EXIT');
  };

  const playCustomSound = async (audioUrl) => {
    if (!isConnected || isMuted) {
      console.log('🔇 Custom sound blocked - disconnected:', !isConnected, 'muted:', isMuted);
      return;
    }

    console.log('🎵 Attempting to play custom sound from URL:', audioUrl);
    
    try {
      // Validate URL
      if (!audioUrl || typeof audioUrl !== 'string') {
        console.error('❌ Invalid audio URL:', audioUrl);
        playDefaultSound();
        return;
      }

      // Create full URL if it's a relative path
      let fullAudioUrl = audioUrl;
      if (audioUrl.startsWith('/')) {
        fullAudioUrl = `${apiBaseUrl}${audioUrl}`;
        console.log('🔗 Converted relative URL to full URL:', fullAudioUrl);
      }

      console.log('🎵 Loading custom audio from:', fullAudioUrl);
      
      const audio = new Audio(fullAudioUrl);
      audio.volume = 0.5;
      
      // Add event listeners for debugging
      audio.addEventListener('loadstart', () => console.log('🎵 Audio loading started'));
      audio.addEventListener('canplay', () => console.log('🎵 Audio can play'));
      audio.addEventListener('canplaythrough', () => console.log('🎵 Audio can play through'));
      audio.addEventListener('error', (e) => console.error('❌ Audio error:', e));
      
      // Wait for audio to be ready
      await new Promise((resolve, reject) => {
        audio.addEventListener('canplaythrough', resolve, { once: true });
        audio.addEventListener('error', reject, { once: true });
        audio.load();
      });
      
      await audio.play();
      console.log('🔊 Custom notification sound played successfully');
      
    } catch (error) {
      console.error('❌ Error playing custom sound:', error);
      console.log('🔄 Falling back to default sound...');
      // Fallback to default sound
      playDefaultSound();
    }
  };

  // Request OS notification permission and show notification
  const showOSNotification = (notification) => {
    console.log('🖥️ showOSNotification called with:', notification);
    
    if (!('Notification' in window)) {
      console.log('❌ This browser does not support OS notifications');
      return;
    }

    console.log('🔍 Current notification permission:', Notification.permission);
    
    if (Notification.permission === 'default') {
      console.log('🔔 Requesting OS notification permission...');
      Notification.requestPermission().then(permission => {
        console.log('🔔 Permission request result:', permission);
        if (permission === 'granted') {
          console.log('✅ Permission granted, showing notification...');
          showNotification(notification);
        } else {
          console.log('❌ Permission denied, cannot show OS notification');
        }
      });
    } else if (Notification.permission === 'granted') {
      console.log('✅ Permission already granted, showing notification...');
      showNotification(notification);
    } else {
      console.log('❌ Permission denied, cannot show OS notification');
    }
  };

  // Request OS notification permissions on component mount
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      console.log('🔔 Requesting OS notification permissions...');
      
      // Show a friendly message about what notifications will contain
      const requestPermission = async () => {
        try {
          const permission = await Notification.requestPermission();
          if (permission === 'granted') {
            console.log('✅ OS notification permissions granted');
            // Show a welcome notification to confirm it's working
            const welcomeNotification = new Notification('🎉 FocusGuard Notifications Enabled!', {
              body: 'You\'ll now receive rich OS notifications for distractions and focus events.',
              icon: '/vite.svg',
              badge: '/vite.svg',
              tag: 'focusguard-welcome',
              requireInteraction: false,
              silent: false
            });
            
            // Auto-close welcome notification after 3 seconds
            setTimeout(() => {
              if (welcomeNotification) {
                welcomeNotification.close();
              }
            }, 3000);
          } else {
            console.log('❌ OS notification permissions denied');
          }
        } catch (error) {
          console.error('❌ Error requesting notification permission:', error);
        }
      };
      
      // Request permission after a short delay to let the user see the app first
      setTimeout(requestPermission, 2000);
    }
    
    // Initialize audio context on mount
    console.log('🔊 Initializing audio context on mount...');
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      console.log('🔊 Audio context initialized:', audioContextRef.current.state);
    }
    
    // Add click listener to resume audio context (required by some browsers)
    const handleUserInteraction = () => {
      if (audioContextRef.current && audioContextRef.current.state === 'suspended') {
        console.log('🔊 User interaction detected, resuming audio context...');
        audioContextRef.current.resume().then(() => {
          console.log('🔊 Audio context resumed after user interaction');
        });
      }
      // Remove listener after first interaction
      document.removeEventListener('click', handleUserInteraction);
    };
    
    document.addEventListener('click', handleUserInteraction);
    
    return () => {
      document.removeEventListener('click', handleUserInteraction);
    };
  }, []);

  const showNotification = (notification) => {
    // Create rich notification title based on type
    let title = 'FocusGuard';
    let icon = '/vite.svg';
    
    if (notification.notification_type === 'distraction') {
      title = '🚨 Distraction Detected!';
      icon = '/vite.svg'; // You can replace with a custom distraction icon
    } else if (notification.notification_type === 'reminder') {
      title = '⏰ Focus Reminder';
      icon = '/vite.svg';
    } else if (notification.notification_type === 'streak') {
      title = '🔥 Focus Streak!';
      icon = '/vite.svg';
    }

    // Create rich notification body with more details
    let body = notification.message;
    
    // Add additional context for distractions
    if (notification.notification_type === 'distraction') {
      if (notification.window_title) {
        body += `\n\n📍 Window: ${notification.window_title}`;
      }
      if (notification.distraction_count && notification.distraction_count > 1) {
        body += `\n\n📊 Distraction #${notification.distraction_count}`;
      }
      if (notification.repeated_notification_count && notification.repeated_notification_count > 0) {
        body += `\n\n🔄 Repeated: ${notification.repeated_notification_count} times`;
      }
    }

    const options = {
      body: body,
      icon: icon,
      badge: icon,
      tag: `focusguard-${notification.notification_type}-${notification.id}`,
      requireInteraction: true, // Keep notification visible until user interacts
      silent: false, // Allow system sound
      data: {
        notificationId: notification.id,
        type: notification.notification_type,
        windowTitle: notification.window_title,
        distractionCount: notification.distraction_count
      }
    };

    try {
      const osNotification = new Notification(title, options);
      
      // Auto-close after 8 seconds for distractions (longer visibility)
      const autoCloseTime = notification.notification_type === 'distraction' ? 8000 : 5000;
      setTimeout(() => {
        if (osNotification) {
          osNotification.close();
        }
      }, autoCloseTime);

      // Handle click - focus the window and close notification
      osNotification.onclick = () => {
        window.focus();
        osNotification.close();
        
        // Log the interaction
        console.log('🖱️ OS notification clicked:', {
          notificationId: notification.id,
          type: notification.notification_type,
          windowTitle: notification.window_title
        });
      };

      // Handle close event
      osNotification.onclose = () => {
        console.log('🔒 OS notification closed:', {
          notificationId: notification.id,
          type: notification.notification_type
        });
      };

      console.log('🖥️ Rich OS notification displayed:', {
        title: title,
        body: body,
        type: notification.notification_type,
        id: notification.id
      });
    } catch (error) {
      console.error('❌ Error showing OS notification:', error);
    }
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'distraction':
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case 'reminder':
        return <Clock className="w-5 h-5 text-blue-500" />;
      case 'streak':
        return <TrendingUp className="w-5 h-5 text-green-500" />;
      default:
        return <Info className="w-5 h-5 text-gray-500" />;
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await fetch(`${apiBaseUrl}/notifications/${notificationId}/read`, {
        method: 'PUT'
      });
      
      setNotifications(prev => 
        prev.map(n => 
          n.id === notificationId ? { ...n, read: true } : n
        )
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      const unreadNotifications = notifications.filter(n => !n.read);
      await Promise.all(
        unreadNotifications.map(n => 
          fetch(`${apiBaseUrl}/notifications/${n.id}/read`, { method: 'PUT' })
        )
      );
      
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
    }
  };

  const getNotificationTypeLabel = (type) => {
    switch (type) {
      case 'distraction':
        return 'Distraction Alert';
      case 'reminder':
        return 'Reminder';
      case 'streak':
        return 'Streak Update';
      default:
        return 'Notification';
    }
  };

  const getNotificationTypeColor = (type) => {
    switch (type) {
      case 'distraction':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'reminder':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'streak':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
  };

  const manualDisconnect = () => {
    console.log('Manual disconnect requested');
    cleanup();
    setIsBackendAvailable(false);
  };

  const manualReconnect = async () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    await connectWebSocket();
  };

  return (
    <div className="relative">
      {/* Connection Status Indicator */}
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
        <span className="text-xs text-gray-600 dark:text-gray-400">
          {isConnected ? 'Connected' : 'Disconnected'}
        </span>
        {!isBackendAvailable && (
          <span className="text-xs text-orange-600 dark:text-orange-400">
            (Backend Unavailable)
          </span>
        )}
      </div>

      {/* Control Buttons */}
      <div className="flex items-center gap-2 mb-3">
        <Button
          variant="outline"
          size="sm"
          onClick={toggleMute}
          className="flex items-center gap-2"
        >
          {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
          {isMuted ? 'Unmute' : 'Mute'}
        </Button>

        {/* Notification Bell */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowNotifications(!showNotifications)}
          className="relative"
        >
          <Bell className="w-5 h-5" />
          {getFilteredUnreadCount() > 0 && (
            <Badge 
              variant="destructive" 
              className="absolute -top-2 -right-2 h-5 w-5 rounded-full p-0 text-xs"
            >
              {getFilteredUnreadCount()}
            </Badge>
          )}
        </Button>
      </div>

      {/* Notifications Panel */}
      {showNotifications && (
        <div className="absolute top-full right-0 mt-2 w-80 bg-white dark:bg-gray-800 border rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
          <div className="p-4 border-b">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">
                {filterType === "today-reminders" ? "Today's Reminders" : "Notifications"}
              </h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowNotifications(false)}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
            {getFilteredNotifications(notifications).length === 0 && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                {filterType === "today-reminders" ? "No reminders today" : "No notifications"}
              </p>
            )}
          </div>
          
          {getFilteredNotifications(notifications).length > 0 && (
            <div className="p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {getFilteredUnreadCount()} unread
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={markAllAsRead}
                  className="text-xs"
                >
                  Mark all as read
                </Button>
              </div>
              
              <div className="space-y-3">
                {getFilteredNotifications(notifications).map((notification) => (
                  <Card key={notification.id} className={`${!notification.read ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : ''}`}>
                    <CardHeader className="pb-2">
                      <div className="flex items-start justify-between">
                        <CardTitle className="text-sm font-medium">
                          {getNotificationTypeLabel(notification.notification_type)}
                        </CardTitle>
                        <Badge 
                          className={`text-xs ${getNotificationTypeColor(notification.notification_type)}`}
                        >
                          {notification.notification_type}
                        </Badge>
                      </div>
                      <CardDescription className="text-xs text-gray-600 dark:text-gray-400">
                        {new Date(notification.created_at).toLocaleString()}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
                        {notification.message}
                      </p>
                      
                      {/* Display distraction count and repeated notification count */}
                      {notification.notification_type === 'distraction' && (
                        <div className="flex items-center gap-2 mb-3 text-xs text-gray-600 dark:text-gray-400">
                          {notification.distraction_count && (
                            <Badge variant="outline" className="text-xs">
                              📊 Distraction #{notification.distraction_count}
                            </Badge>
                          )}
                          {notification.repeated_notification_count && notification.repeated_notification_count > 0 && (
                            <Badge variant="outline" className="text-xs">
                              🔄 Repeated: {notification.repeated_notification_count} times
                            </Badge>
                          )}
                        </div>
                      )}
                      
                      {!notification.read && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => markAsRead(notification.id)}
                          className="w-full"
                        >
                          Mark as Read
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationCenter; 