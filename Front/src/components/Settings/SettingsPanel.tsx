import { useState } from 'react';
import { Bell, Shield, User, Database, Moon, Palette, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

export default function SettingsPanel() {
  const [settings, setSettings] = useState({
    notifications: {
      emailAlerts: true,
      pushNotifications: true,
      analysisComplete: true,
      weeklyReports: false
    },
    preferences: {
      theme: 'dark',
      language: 'en',
      timezone: 'UTC-8',
      riskThreshold: '7'
    },
    profile: {
      name: 'Elyes Tayechi',
      email: 'tayechielyes3@gmail.com',
      role: 'Hedha test lel pipeline tee'
    }
  });

  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    // Simulate API call
    setTimeout(() => {
      setIsSaving(false);
    }, 1000);
  };

  const updateSetting = (category: string, key: string, value: string | boolean) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category as keyof typeof prev],
        [key]: value
      }
    }));
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Settings</h2>
        <Button
          onClick={handleSave}
          disabled={isSaving}
          className="bg-blue-600 hover:bg-blue-700 text-white flex items-center space-x-2 text-sm"
        >
          {isSaving ? (
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
          ) : (
            <Save className="w-4 h-4" />
          )}
          <span>{isSaving ? 'Saving...' : 'Save Changes'}</span>
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Profile Settings */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
          <div className="flex items-center space-x-2 mb-5">
            <User className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <h3 className="text-base font-semibold text-gray-900 dark:text-white">Profile</h3>
          </div>

          <div className="space-y-4">
            <div>
              <Label htmlFor="name" className="text-sm font-medium text-gray-900 dark:text-white mb-2 block">
                Full Name
              </Label>
              <Input
                id="name"
                value={settings.profile.name}
                onChange={(e) => updateSetting('profile', 'name', e.target.value)}
                className="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white text-sm"
              />
            </div>

            <div>
              <Label htmlFor="email" className="text-sm font-medium text-gray-900 dark:text-white mb-2 block">
                Email Address
              </Label>
              <Input
                id="email"
                type="email"
                value={settings.profile.email}
                onChange={(e) => updateSetting('profile', 'email', e.target.value)}
                className="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white text-sm"
              />
            </div>

            <div>
              <Label htmlFor="role" className="text-sm font-medium text-gray-900 dark:text-white mb-2 block">
                Role
              </Label>
              <Input
                id="role"
                value={settings.profile.role}
                onChange={(e) => updateSetting('profile', 'role', e.target.value)}
                className="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white text-sm"
              />
            </div>
          </div>
        </div>

        {/* Notification Settings */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
          <div className="flex items-center space-x-2 mb-5">
            <Bell className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <h3 className="text-base font-semibold text-gray-900 dark:text-white">Notifications</h3>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-gray-900 dark:text-white font-medium text-sm">Email Alerts</div>
                <div className="text-gray-500 dark:text-gray-400 text-xs">Receive email notifications for important updates</div>
              </div>
              <Switch
                checked={settings.notifications.emailAlerts}
                onCheckedChange={(checked) => updateSetting('notifications', 'emailAlerts', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="text-gray-900 dark:text-white font-medium text-sm">Push Notifications</div>
                <div className="text-gray-500 dark:text-gray-400 text-xs">Browser push notifications</div>
              </div>
              <Switch
                checked={settings.notifications.pushNotifications}
                onCheckedChange={(checked) => updateSetting('notifications', 'pushNotifications', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="text-gray-900 dark:text-white font-medium text-sm">Analysis Complete</div>
                <div className="text-gray-500 dark:text-gray-400 text-xs">Notify when analysis is finished</div>
              </div>
              <Switch
                checked={settings.notifications.analysisComplete}
                onCheckedChange={(checked) => updateSetting('notifications', 'analysisComplete', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="text-gray-900 dark:text-white font-medium text-sm">Weekly Reports</div>
                <div className="text-gray-500 dark:text-gray-400 text-xs">Summary of weekly activity</div>
              </div>
              <Switch
                checked={settings.notifications.weeklyReports}
                onCheckedChange={(checked) => updateSetting('notifications', 'weeklyReports', checked)}
              />
            </div>
          </div>
        </div>

        {/* Preferences */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
          <div className="flex items-center space-x-2 mb-5">
            <Palette className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <h3 className="text-base font-semibold text-gray-900 dark:text-white">Preferences</h3>
          </div>

          <div className="space-y-4">
            <div>
              <Label className="text-sm font-medium text-gray-900 dark:text-white mb-2 block">
                Language
              </Label>
              <Select 
                value={settings.preferences.language} 
                onValueChange={(value) => updateSetting('preferences', 'language', value)}
              >
                <SelectTrigger className="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white">
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="es">Spanish</SelectItem>
                  <SelectItem value="fr">French</SelectItem>
                  <SelectItem value="de">German</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-sm font-medium text-gray-900 dark:text-white mb-2 block">
                Risk Threshold
              </Label>
              <Select 
                value={settings.preferences.riskThreshold} 
                onValueChange={(value) => updateSetting('preferences', 'riskThreshold', value)}
              >
                <SelectTrigger className="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white">
                  <SelectItem value="5">Conservative (5.0)</SelectItem>
                  <SelectItem value="7">Moderate (7.0)</SelectItem>
                  <SelectItem value="8">Aggressive (8.0)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

      
      </div>
    </div>
  );
}