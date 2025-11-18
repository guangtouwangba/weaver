import React, { useState } from 'react'
import Avatar from './Avatar'
import Button from './Button'
import Card from './Card'
import Chip from './Chip'
import Input from './Input'
import Tabs from './Tabs'
import ProgressBar from './ProgressBar'
import ListItem from './ListItem'
import Toggle from './Toggle'

export const PersonalCenter = ({ 
  user = {},
  stats = {},
  activities = [],
  settings = {},
  onUpdateProfile,
  onUpdateSettings,
  ...props 
}) => {
  const [activeTab, setActiveTab] = useState(0)
  const [editMode, setEditMode] = useState(false)

  const tabs = ['Profile', 'Settings', 'Activity', 'Preferences']

  return (
    <div className="bg-surface-page min-h-screen" {...props}>
      <div className="max-w-[1280px] mx-auto px-lg py-xl">
        
        {/* Profile Header */}
        <Card>
          <div className="flex items-start gap-6">
            <div className="relative flex-shrink-0">
              <div className="w-24 h-24">
                <Avatar 
                  src={user.avatar}
                  fallback={user.name?.charAt(0) || 'U'}
                  size="lg"
                />
              </div>
              <button 
                className="absolute bottom-0 right-0 w-8 h-8 bg-primary-strong text-text-on-accent rounded-full flex items-center justify-center hover:bg-primary-hover active:bg-primary-pressed transition-all shadow-soft"
                title="Change profile picture"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>
            </div>
            
            <div className="flex-1">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h1 className="text-display-md font-semibold text-text-primary mb-1">
                    {user.name || 'User Name'}
                  </h1>
                  <p className="text-body text-text-secondary mb-2">
                    {user.email || 'user@example.com'}
                  </p>
                  <div className="flex gap-2">
                    <Chip variant="active">{user.role || 'Member'}</Chip>
                    <Chip variant="confirmed">Verified</Chip>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <Button 
                    variant="secondary" 
                    onClick={() => setEditMode(!editMode)}
                  >
                    {editMode ? 'Cancel' : 'Edit Profile'}
                  </Button>
                  <Button variant="primary">Share Profile</Button>
                </div>
              </div>
              
              <div className="mt-4 pt-4 border-t border-border-subtle">
                <div className="grid grid-cols-4 gap-6">
                  <div>
                    <div className="text-display-md font-semibold text-text-primary">
                      {stats.projects || 0}
                    </div>
                    <div className="text-caption text-text-secondary">Projects</div>
                  </div>
                  <div>
                    <div className="text-display-md font-semibold text-text-primary">
                      {stats.conversations || 0}
                    </div>
                    <div className="text-caption text-text-secondary">Conversations</div>
                  </div>
                  <div>
                    <div className="text-display-md font-semibold text-text-primary">
                      {stats.contributions || 0}
                    </div>
                    <div className="text-caption text-text-secondary">Contributions</div>
                  </div>
                  <div>
                    <div className="text-display-md font-semibold text-text-primary">
                      {stats.followers || 0}
                    </div>
                    <div className="text-caption text-text-secondary">Followers</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* Tabs Navigation */}
        <div className="mt-xl">
          <Tabs tabs={tabs} defaultTab={activeTab} onChange={setActiveTab} />
        </div>

        {/* Tab Content */}
        <div className="mt-lg">
          {activeTab === 0 && (
            <div className="space-y-lg">
              {/* Profile Information */}
              <Card title="Profile Information">
                <div className="space-y-md max-w-2xl">
                  <div className="grid grid-cols-2 gap-md">
                    <Input 
                      label="First Name"
                      placeholder="John"
                      defaultValue={user.firstName}
                      disabled={!editMode}
                    />
                    <Input 
                      label="Last Name"
                      placeholder="Doe"
                      defaultValue={user.lastName}
                      disabled={!editMode}
                    />
                  </div>
                  
                  <Input 
                    label="Email Address"
                    type="email"
                    placeholder="john@example.com"
                    defaultValue={user.email}
                    disabled={!editMode}
                  />
                  
                  <Input 
                    label="Phone Number"
                    placeholder="+1 (555) 000-0000"
                    defaultValue={user.phone}
                    disabled={!editMode}
                  />
                  
                  <div>
                    <label className="block text-caption text-text-secondary mb-1 font-medium">
                      Bio
                    </label>
                    <textarea
                      className="w-full px-3 py-2 bg-surface-card border border-border-subtle rounded-md text-body resize-none outline-none focus:border-border-focus focus:ring-2 focus:ring-primary-soft transition-all placeholder:text-text-muted disabled:opacity-50"
                      rows={4}
                      placeholder="Tell us about yourself..."
                      defaultValue={user.bio}
                      disabled={!editMode}
                    />
                  </div>
                  
                  {editMode && (
                    <div className="flex gap-2 pt-2">
                      <Button variant="primary">Save Changes</Button>
                      <Button variant="secondary" onClick={() => setEditMode(false)}>
                        Cancel
                      </Button>
                    </div>
                  )}
                </div>
              </Card>

              {/* Account Progress */}
              <Card title="Account Progress">
                <div className="space-y-lg">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-body text-text-primary">Profile Completion</span>
                      <span className="text-body-bold text-primary-strong">85%</span>
                    </div>
                    <ProgressBar value={85} color="primary" />
                    <p className="text-caption text-text-muted mt-2">
                      Add your phone number and bio to complete your profile
                    </p>
                  </div>
                  
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-body text-text-primary">Storage Used</span>
                      <span className="text-body-bold text-emerald-strong">2.4 GB / 5 GB</span>
                    </div>
                    <ProgressBar value={48} color="emerald" />
                  </div>
                </div>
              </Card>
            </div>
          )}

          {activeTab === 1 && (
            <div className="space-y-lg">
              {/* Account Settings */}
              <Card title="Account Settings">
                <div className="space-y-md max-w-2xl">
                  <Input 
                    label="Username"
                    placeholder="johndoe"
                    defaultValue={user.username}
                  />
                  
                  <Input 
                    label="Current Password"
                    type="password"
                    placeholder="Enter current password"
                  />
                  
                  <Input 
                    label="New Password"
                    type="password"
                    placeholder="Enter new password"
                  />
                  
                  <Input 
                    label="Confirm New Password"
                    type="password"
                    placeholder="Confirm new password"
                  />
                  
                  <div className="flex gap-2 pt-2">
                    <Button variant="primary">Update Password</Button>
                  </div>
                </div>
              </Card>

              {/* Privacy Settings */}
              <Card title="Privacy Settings">
                <div className="divide-y divide-border-subtle">
                  <Toggle
                    label="Profile Visibility"
                    description="Make your profile visible to others"
                    checked={true}
                  />
                  
                  <Toggle
                    label="Show Email"
                    description="Display email address on profile"
                    checked={false}
                  />
                  
                  <Toggle
                    label="Activity Status"
                    description="Show when you're active"
                    checked={true}
                  />
                </div>
              </Card>

              {/* Danger Zone */}
              <Card title="Danger Zone">
                <div className="space-y-4">
                  <div className="flex items-center justify-between py-2">
                    <div>
                      <div className="text-body font-medium text-red-strong">Delete Account</div>
                      <div className="text-caption text-text-secondary">Permanently delete your account and all data</div>
                    </div>
                    <Button variant="secondary">Delete Account</Button>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {activeTab === 2 && (
            <Card title="Recent Activity">
              <div className="border border-border-subtle rounded-md overflow-hidden">
                {activities.length === 0 ? (
                  <div className="py-12 text-center">
                    <span className="text-4xl mb-3 block">📊</span>
                    <p className="text-body text-text-secondary">No recent activity</p>
                  </div>
                ) : (
                  activities.map((activity, index) => (
                    <ListItem
                      key={index}
                      avatar={<Avatar fallback={activity.icon} size="md" />}
                      title={activity.title}
                      subtitle={activity.timestamp}
                      status={<Chip variant={activity.status}>{activity.statusLabel}</Chip>}
                    />
                  ))
                )}
              </div>
            </Card>
          )}

          {activeTab === 3 && (
            <div className="space-y-lg">
              {/* Notification Preferences */}
              <Card title="Notification Preferences">
                <div className="divide-y divide-border-subtle">
                  <Toggle
                    label="Email Notifications"
                    description="Receive notifications via email"
                    checked={true}
                  />
                  
                  <Toggle
                    label="Push Notifications"
                    description="Receive push notifications"
                    checked={true}
                  />
                  
                  <Toggle
                    label="SMS Notifications"
                    description="Receive text messages for important updates"
                    checked={false}
                  />
                </div>
              </Card>

              {/* Appearance */}
              <Card title="Appearance">
                <div className="space-y-4">
                  <div>
                    <label className="block text-caption text-text-secondary mb-2 font-medium">
                      Theme
                    </label>
                    <div className="flex gap-2">
                      <Button variant="primary">Light</Button>
                      <Button variant="secondary">Dark</Button>
                      <Button variant="secondary">Auto</Button>
                    </div>
                  </div>
                  
                  <div className="pt-2">
                    <label className="block text-caption text-text-secondary mb-2 font-medium">
                      Language
                    </label>
                    <select className="w-full max-w-xs px-3 h-10 bg-surface-card border border-border-subtle rounded-md text-body outline-none focus:border-border-focus focus:ring-2 focus:ring-primary-soft transition-all">
                      <option>English</option>
                      <option>Spanish</option>
                      <option>French</option>
                      <option>German</option>
                      <option>Chinese</option>
                    </select>
                  </div>
                </div>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default PersonalCenter

