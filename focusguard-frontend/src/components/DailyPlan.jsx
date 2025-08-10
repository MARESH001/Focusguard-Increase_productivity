import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Checkbox } from './ui/checkbox';
import { Badge } from './ui/badge';
import { 
  ArrowLeft, 
  Calendar, 
  CheckCircle2, 
  Clock, 
  Save,
  Plus,
  Trash2,
  Edit3,
  Bell,
  AlarmClock
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const DailyPlan = ({ user, apiBaseUrl }) => {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [isCompleted, setIsCompleted] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setSaving] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [newTaskText, setNewTaskText] = useState('');
  const [newReminderText, setNewReminderText] = useState('');
  const [newReminderTime, setNewReminderTime] = useState('');

  useEffect(() => {
    loadPlan(selectedDate);
  }, [selectedDate]);

  const loadPlan = async (date) => {
    try {
      const response = await fetch(`${apiBaseUrl}/users/${user.username}/plans/enhanced/${date}`);
      if (response.ok) {
        const plan = await response.json();
        setTasks(plan.tasks || []);
        setReminders(plan.reminders || []);
        setIsCompleted(plan.completed);
        setIsEditing(false);
      } else {
        // No plan exists for this date
        setTasks([]);
        setReminders([]);
        setIsCompleted(false);
        setIsEditing(true);
      }
    } catch (error) {
      console.error('Error loading plan:', error);
      setTasks([]);
      setReminders([]);
      setIsCompleted(false);
      setIsEditing(true);
    }
  };

  const savePlan = async () => {
    setSaving(true);
    try {
      const planData = {
        tasks: tasks,
        reminders: reminders
      };
      
      console.log('🔄 Saving plan data:', planData);
      console.log('📊 Current tasks count:', tasks.length);
      console.log('⏰ Current reminders count:', reminders.length);
      
      const response = await fetch(`${apiBaseUrl}/users/${user.username}/plans/enhanced/${selectedDate}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(planData),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('✅ Plan saved successfully:', result);
        setIsEditing(false);
        // Reload to get updated data
        await loadPlan(selectedDate);
      } else {
        console.error('❌ Failed to save plan:', response.status, response.statusText);
        const errorText = await response.text();
        console.error('Error details:', errorText);
      }
    } catch (error) {
      console.error('❌ Error saving plan:', error);
    } finally {
      setSaving(false);
    }
  };

  const toggleTaskCompletion = async (taskId) => {
    setTasks(prevTasks => 
      prevTasks.map(task => 
        task.id === taskId 
          ? { ...task, completed: !task.completed }
          : task
      )
    );
    // Auto-save after toggling task completion
    await savePlan();
  };

  const addTask = async () => {
    if (!newTaskText.trim()) return;
    
    console.log('➕ Adding new task:', newTaskText.trim());
    console.log('📋 Current tasks before adding:', tasks);
    
    const newTask = {
      id: Date.now().toString(),
      text: newTaskText.trim(),
      completed: false
    };
    
    console.log('📝 New task object:', newTask);
    
    const updatedTasks = [...tasks, newTask];
    console.log('📋 Tasks after adding:', updatedTasks);
    
    setTasks(updatedTasks);
    setNewTaskText('');
    
    // Save with the updated tasks array
    await savePlanWithData(updatedTasks, reminders);
  };

  const removeTask = async (taskId) => {
    console.log('🗑️ Removing task with ID:', taskId);
    console.log('📋 Tasks before removal:', tasks);
    
    const updatedTasks = tasks.filter(task => task.id !== taskId);
    console.log('📋 Tasks after removal:', updatedTasks);
    
    setTasks(updatedTasks);
    
    // Save with the updated tasks array
    await savePlanWithData(updatedTasks, reminders);
  };

  const addReminder = async () => {
    if (!newReminderText.trim() || !newReminderTime) return;
    
    console.log('➕ Adding new reminder:', newReminderText.trim(), 'at', newReminderTime);
    console.log('⏰ Current reminders before adding:', reminders);
    
    const newReminder = {
      id: Date.now().toString(),
      text: newReminderText.trim(),
      time: newReminderTime,
      completed: false
    };
    
    console.log('📝 New reminder object:', newReminder);
    
    const updatedReminders = [...reminders, newReminder];
    console.log('⏰ Reminders after adding:', updatedReminders);
    
    setReminders(updatedReminders);
    setNewReminderText('');
    setNewReminderTime('');
    
    // Save with the updated reminders array
    await savePlanWithData(tasks, updatedReminders);
  };

  const removeReminder = async (reminderId) => {
    console.log('🗑️ Removing reminder with ID:', reminderId);
    console.log('⏰ Reminders before removal:', reminders);
    
    const updatedReminders = reminders.filter(reminder => reminder.id !== reminderId);
    console.log('⏰ Reminders after removal:', updatedReminders);
    
    setReminders(updatedReminders);
    
    // Save with the updated reminders array
    await savePlanWithData(tasks, updatedReminders);
  };

  const toggleReminderCompletion = async (reminderId) => {
    setReminders(prevReminders => 
      prevReminders.map(reminder => 
        reminder.id === reminderId 
          ? { ...reminder, completed: !reminder.completed }
          : reminder
      )
    );
    // Auto-save after toggling reminder completion
    await savePlan();
  };

  const savePlanWithData = async (tasksToSave, remindersToSave) => {
    setSaving(true);
    try {
      const planData = {
        tasks: tasksToSave,
        reminders: remindersToSave
      };
      
      console.log('🔄 Saving plan data:', planData);
      console.log('📊 Tasks to save count:', tasksToSave.length);
      console.log('⏰ Reminders to save count:', remindersToSave.length);
      
      const response = await fetch(`${apiBaseUrl}/users/${user.username}/plans/enhanced/${selectedDate}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(planData),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('✅ Plan saved successfully:', result);
        setIsEditing(false);
        // Reload to get updated data
        await loadPlan(selectedDate);
      } else {
        console.error('❌ Failed to save plan:', response.status, response.statusText);
        const errorText = await response.text();
        console.error('Error details:', errorText);
      }
    } catch (error) {
      console.error('❌ Error saving plan:', error);
    } finally {
      setSaving(false);
    }
  };

  const getDateOptions = () => {
    const dates = [];
    const today = new Date();
    
    // Add past 7 days and next 7 days
    for (let i = -7; i <= 7; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      dates.push({
        value: date.toISOString().split('T')[0],
        label: i === 0 ? 'Today' : 
               i === -1 ? 'Yesterday' :
               i === 1 ? 'Tomorrow' :
               date.toLocaleDateString('en-US', { 
                 weekday: 'short', 
                 month: 'short', 
                 day: 'numeric' 
               })
      });
    }
    
    return dates;
  };

  const isToday = selectedDate === new Date().toISOString().split('T')[0];
  const isPast = new Date(selectedDate) < new Date(new Date().toISOString().split('T')[0]);
  const isFuture = new Date(selectedDate) > new Date(new Date().toISOString().split('T')[0]);
  const completedTasks = tasks.filter(task => task.completed).length;
  const totalTasks = tasks.length;
  const completedReminders = reminders.filter(reminder => reminder.completed).length;
  const totalReminders = reminders.length;

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Button variant="outline" onClick={() => navigate('/')} className="hover-glow">
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Daily Planning</h1>
            <p className="text-muted-foreground">Plan your day with tasks and reminders</p>
          </div>
        </div>

        {/* Date Selector */}
        <Card className="hover-glow">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Select Date
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 md:grid-cols-5 gap-2">
              {getDateOptions().map((date) => (
                <Button
                  key={date.value}
                  variant={selectedDate === date.value ? "default" : "outline"}
                  onClick={() => setSelectedDate(date.value)}
                  className="text-sm hover-glow"
                >
                  {date.label}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Plan Editor/Viewer */}
        <Card className="hover-glow">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  {isToday ? '📅 Today\'s Plan' : 
                   isPast ? '📋 Past Plan' : 
                   '📝 Future Plan'}
                  {(totalTasks > 0 || totalReminders > 0) && (
                    <Badge className="bg-blue-600">
                      {completedTasks + completedReminders}/{totalTasks + totalReminders} completed
                    </Badge>
                  )}
                </CardTitle>
                <CardDescription>
                  {new Date(selectedDate).toLocaleDateString('en-US', { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                  })}
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                {!isEditing && (tasks.length > 0 || reminders.length > 0) && (
                  <>
                    <Button
                      variant="outline"
                      onClick={() => setIsEditing(true)}
                      className="hover-glow"
                    >
                      <Edit3 className="h-4 w-4" />
                    </Button>
                    {isToday && (
                      <Button
                        variant={isCompleted ? "secondary" : "default"}
                        onClick={() => setIsCompleted(!isCompleted)}
                        className="hover-glow"
                      >
                        {isCompleted ? (
                          <>
                            <Clock className="h-4 w-4 mr-2" />
                            Mark Incomplete
                          </>
                        ) : (
                          <>
                            <CheckCircle2 className="h-4 w-4 mr-2" />
                            Mark Complete
                          </>
                        )}
                      </Button>
                    )}
                  </>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {isEditing ? (
              <div className="space-y-6">
                {/* Tasks Section */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5" />
                    Tasks
                  </h3>
                  
                  {/* Add New Task */}
                  <div className="flex gap-2">
                    <Input
                      placeholder="Enter task description..."
                      value={newTaskText}
                      onChange={(e) => setNewTaskText(e.target.value)}
                      className="flex-1"
                    />
                    <Button onClick={addTask} disabled={!newTaskText.trim()}>
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>

                  {/* Task List */}
                  {tasks.length === 0 ? (
                    <p className="text-muted-foreground text-center py-4">
                      No tasks yet. Add your first task above!
                    </p>
                  ) : (
                    tasks.map((task) => (
                      <div key={task.id} className="flex items-center gap-3 p-3 border rounded-lg">
                        <Checkbox
                          checked={task.completed}
                          onCheckedChange={() => toggleTaskCompletion(task.id)}
                        />
                        <div className="flex-1">
                          <span className={task.completed ? 'line-through text-muted-foreground' : ''}>
                            {task.text}
                          </span>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => removeTask(task.id)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    ))
                  )}
                </div>

                {/* Reminders Section */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold flex items-center gap-2">
                    <AlarmClock className="h-5 w-5" />
                    Reminders
                  </h3>
                  
                  {/* Add New Reminder */}
                  <div className="flex gap-2">
                    <Input
                      placeholder="Enter reminder description..."
                      value={newReminderText}
                      onChange={(e) => setNewReminderText(e.target.value)}
                      className="flex-1"
                    />
                    <Input
                      type="time"
                      value={newReminderTime}
                      onChange={(e) => setNewReminderTime(e.target.value)}
                      className="w-32"
                    />
                    <Button onClick={addReminder} disabled={!newReminderText.trim() || !newReminderTime}>
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>

                  {/* Reminder List */}
                  {reminders.length === 0 ? (
                    <p className="text-muted-foreground text-center py-4">
                      No reminders yet. Add your first reminder above!
                    </p>
                  ) : (
                    reminders.map((reminder) => (
                      <div key={reminder.id} className="flex items-center gap-3 p-3 border rounded-lg">
                        <Checkbox
                          checked={reminder.completed}
                          onCheckedChange={() => toggleReminderCompletion(reminder.id)}
                        />
                        <div className="flex-1">
                          <span className={reminder.completed ? 'line-through text-muted-foreground' : ''}>
                            {reminder.text}
                          </span>
                          <div className="flex items-center gap-1 mt-1">
                            <Bell className="h-3 w-3 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">
                              {reminder.time}
                            </span>
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => removeReminder(reminder.id)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    ))
                  )}
                </div>

                {/* Save/Cancel Buttons */}
                <div className="flex items-center gap-2">
                  <Button 
                    onClick={savePlan}
                    disabled={(tasks.length === 0 && reminders.length === 0) || isSaving}
                    className="hover-glow"
                  >
                    {isSaving ? (
                      <div className="flex items-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                        Saving...
                      </div>
                    ) : (
                      <>
                        <Save className="h-4 w-4 mr-2" />
                        Save Plan
                      </>
                    )}
                  </Button>
                  {(tasks.length > 0 || reminders.length > 0) && (
                    <Button 
                      variant="outline"
                      onClick={() => {
                        setIsEditing(false);
                        loadPlan(selectedDate); // Reload original plan
                      }}
                      className="hover-glow"
                    >
                      Cancel
                    </Button>
                  )}
                </div>
              </div>
            ) : (tasks.length > 0 || reminders.length > 0) ? (
              <div className="space-y-6">
                {/* Tasks Section */}
                {tasks.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                      <CheckCircle2 className="h-5 w-5" />
                      Tasks
                    </h3>
                    {tasks.map((task) => (
                      <div key={task.id} className="flex items-center gap-3 p-3 border rounded-lg">
                        <Checkbox
                          checked={task.completed}
                          disabled={!isToday}
                          onCheckedChange={() => toggleTaskCompletion(task.id)}
                        />
                        <div className="flex-1">
                          <span className={task.completed ? 'line-through text-muted-foreground' : ''}>
                            {task.text}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Reminders Section */}
                {reminders.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                      <AlarmClock className="h-5 w-5" />
                      Reminders
                    </h3>
                    {reminders.map((reminder) => (
                      <div key={reminder.id} className="flex items-center gap-3 p-3 border rounded-lg">
                        <Checkbox
                          checked={reminder.completed}
                          disabled={!isToday}
                          onCheckedChange={() => toggleReminderCompletion(reminder.id)}
                        />
                        <div className="flex-1">
                          <span className={reminder.completed ? 'line-through text-muted-foreground' : ''}>
                            {reminder.text}
                          </span>
                          <div className="flex items-center gap-1 mt-1">
                            <Bell className="h-3 w-3 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">
                              Reminder at {reminder.time}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {isToday && (completedTasks < totalTasks || completedReminders < totalReminders) && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Clock className="h-4 w-4" />
                    Ready to start working on your tasks? 
                    <Button 
                      variant="link" 
                      className="p-0 h-auto text-primary"
                      onClick={() => navigate('/timer')}
                    >
                      Start a focus session
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12">
                <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="text-muted-foreground mb-4">
                  No tasks or reminders set for this date
                </p>
                <Button 
                  onClick={() => setIsEditing(true)}
                  className="hover-glow"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Create Plan
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Planning Tips */}
        <Card className="hover-glow">
          <CardHeader>
            <CardTitle>💡 Planning Tips</CardTitle>
            <CardDescription>
              Make the most of your daily planning
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
              <div className="space-y-3">
                <h4 className="font-semibold">🎯 Task Management</h4>
                <ul className="space-y-2 text-muted-foreground">
                  <li>• Break large tasks into smaller, manageable items</li>
                  <li>• Set specific, actionable task descriptions</li>
                  <li>• Prioritize your most important tasks</li>
                  <li>• Review and adjust your task list regularly</li>
                  <li>• Check off tasks as you complete them</li>
                </ul>
              </div>
              <div className="space-y-3">
                <h4 className="font-semibold">⏰ Reminder System</h4>
                <ul className="space-y-2 text-muted-foreground">
                  <li>• Set reminders for time-sensitive tasks</li>
                  <li>• Use reminders to stay on track</li>
                  <li>• Set realistic expectations for daily tasks</li>
                  <li>• Use focus sessions to work on planned tasks</li>
                  <li>• Review your plan at the start of each day</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="hover-glow">
            <CardContent className="pt-6">
              <div className="text-center space-y-3">
                <div className="p-3 rounded-full bg-primary/10 w-fit mx-auto">
                  <Clock className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-semibold">Start Focus Session</h3>
                <p className="text-sm text-muted-foreground">
                  Begin working on your planned tasks with a focused session
                </p>
                <Button 
                  onClick={() => navigate('/timer')}
                  className="w-full hover-glow"
                >
                  Start Session
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="hover-glow">
            <CardContent className="pt-6">
              <div className="text-center space-y-3">
                <div className="p-3 rounded-full bg-primary/10 w-fit mx-auto">
                  <CheckCircle2 className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-semibold">View Progress</h3>
                <p className="text-sm text-muted-foreground">
                  Track your progress and see how well you're completing tasks
                </p>
                <Button 
                  variant="outline"
                  onClick={() => navigate('/stats')}
                  className="w-full hover-glow"
                >
                  View Stats
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default DailyPlan;

