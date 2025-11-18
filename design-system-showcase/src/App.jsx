import React, { useState } from 'react'
import Button from './components/Button'
import Chip from './components/Chip'
import Card from './components/Card'
import ListItem from './components/ListItem'
import Tabs from './components/Tabs'
import Input from './components/Input'
import Banner from './components/Banner'
import ProgressBar from './components/ProgressBar'
import Avatar, { AvatarGroup } from './components/Avatar'
import EmptyState from './components/EmptyState'
import MetricCard from './components/MetricCard'
import ChatBox from './components/ChatBox'
import PersonalCenter from './components/PersonalCenter'
import Toggle from './components/Toggle'
import TokenizedInput from './components/TokenizedInput'
import Select from './components/Select'
import Modal from './components/Modal'
import Dropdown from './components/Dropdown'
import Icon from './components/Icon'

function App() {
  const [currentView, setCurrentView] = useState('showcase')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedCountry, setSelectedCountry] = useState('')
  const [tokens, setTokens] = useState([
    { label: 'Design', avatar: { fallback: 'D' } },
    { label: 'Development', avatar: { fallback: 'D' } },
  ])
  const [chatMessages, setChatMessages] = useState([
    {
      message: "Hey! How's the project going?",
      sender: "Alice Smith",
      timestamp: "10:30 AM",
      isOwn: false,
      avatar: { fallback: "AS" }
    },
    {
      message: "Going great! Just finished the design system components.",
      sender: "You",
      timestamp: "10:32 AM",
      isOwn: true,
      avatar: { fallback: "JD" }
    },
    {
      message: "That's awesome! Can't wait to see them in action.",
      sender: "Alice Smith",
      timestamp: "10:33 AM",
      isOwn: false,
      avatar: { fallback: "AS" }
    }
  ])

  const handleSendMessage = (message) => {
    setChatMessages([...chatMessages, {
      message,
      sender: "You",
      timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      isOwn: true,
      avatar: { fallback: "JD" }
    }])
  }

  if (currentView === 'personal-center') {
    return (
      <div>
        <div className="bg-surface-card shadow-soft border-b border-border-subtle">
          <div className="max-w-[1280px] mx-auto px-lg py-md">
            <div className="flex items-center justify-between">
              <Button variant="ghost" onClick={() => setCurrentView('showcase')}>
                ← Back to Showcase
              </Button>
              <h1 className="text-display-md font-semibold text-text-primary">
                Personal Center
              </h1>
              <div className="w-24"></div>
            </div>
          </div>
        </div>
        <PersonalCenter 
          user={{
            name: "John Doe",
            email: "john.doe@example.com",
            firstName: "John",
            lastName: "Doe",
            username: "johndoe",
            role: "Admin",
            phone: "+1 (555) 123-4567",
            bio: "Product designer passionate about creating delightful user experiences."
          }}
          stats={{
            projects: 24,
            conversations: 156,
            contributions: 892,
            followers: 1240
          }}
          activities={[
            {
              icon: "✏️",
              title: "Updated project 'Design System'",
              timestamp: "2 hours ago",
              status: "active",
              statusLabel: "Active"
            },
            {
              icon: "✓",
              title: "Completed milestone 'Component Library'",
              timestamp: "1 day ago",
              status: "confirmed",
              statusLabel: "Done"
            },
            {
              icon: "💬",
              title: "Commented on 'User Flow Redesign'",
              timestamp: "2 days ago",
              status: "info",
              statusLabel: "Comment"
            }
          ]}
        />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-surface-page">
      {/* Header */}
      <div className="bg-surface-card shadow-soft border-b border-border-subtle">
        <div className="max-w-[1280px] mx-auto px-lg py-md">
          <div className="flex items-center justify-between">
            <h1 className="text-display-lg font-semibold text-text-primary">
              Design System Showcase
            </h1>
            <div className="flex items-center gap-3">
              <Button variant="ghost">Documentation</Button>
              <Button variant="secondary">Settings</Button>
              <button onClick={() => setCurrentView('personal-center')}>
                <Avatar fallback="JD" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-[1280px] mx-auto px-lg py-xl space-y-xl">
        
        {/* Metrics Section */}
        <section>
          <h2 className="text-display-md font-semibold text-text-primary mb-lg">Metrics & Stats</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-lg">
            <MetricCard 
              value="2,847" 
              label="Total Users" 
              change="+12% from last month"
              changeType="positive"
              icon={<span className="text-xl">👥</span>}
            />
            <MetricCard 
              value="$45.2K" 
              label="Revenue" 
              change="+8.2% from last month"
              changeType="positive"
              icon={<span className="text-xl">💰</span>}
            />
            <MetricCard 
              value="94.5%" 
              label="Satisfaction" 
              change="-2.1% from last month"
              changeType="negative"
              icon={<span className="text-xl">⭐</span>}
            />
            <MetricCard 
              value="1,429" 
              label="Active Sessions" 
              change="No change"
              changeType="neutral"
              icon={<span className="text-xl">🔥</span>}
            />
          </div>
        </section>

        {/* Buttons Section */}
        <section>
          <h2 className="text-display-md font-semibold text-text-primary mb-lg">Buttons</h2>
          <Card title="Button Variants">
            <div className="space-y-md">
              <div>
                <p className="text-caption text-text-secondary mb-sm">Primary Buttons</p>
                <div className="flex flex-wrap gap-xs">
                  <Button variant="primary">Start Conversation</Button>
                  <Button variant="primary" icon={<span>+</span>}>Create New</Button>
                  <Button variant="primary" disabled>Disabled</Button>
                </div>
              </div>
              
              <div>
                <p className="text-caption text-text-secondary mb-sm">Secondary Buttons</p>
                <div className="flex flex-wrap gap-xs">
                  <Button variant="secondary">Cancel</Button>
                  <Button variant="secondary" icon={<span>⚙️</span>}>Settings</Button>
                  <Button variant="secondary" disabled>Disabled</Button>
                </div>
              </div>
              
              <div>
                <p className="text-caption text-text-secondary mb-sm">Ghost Buttons</p>
                <div className="flex flex-wrap gap-xs">
                  <Button variant="ghost">View More</Button>
                  <Button variant="ghost" icon={<span>→</span>} iconPosition="right">Next</Button>
                </div>
              </div>
              
              <div>
                <p className="text-caption text-text-secondary mb-sm">Tiny Buttons</p>
                <div className="flex flex-wrap gap-xs">
                  <Button variant="tiny">Tag</Button>
                  <Button variant="tiny">Filter</Button>
                  <Button variant="tiny">Sort</Button>
                </div>
              </div>
            </div>
          </Card>
        </section>

        {/* Chips & Tags Section */}
        <section>
          <h2 className="text-display-md font-semibold text-text-primary mb-lg">Chips & Tags</h2>
          <Card title="Status Chips">
            <div className="space-y-md">
              <div>
                <p className="text-caption text-text-secondary mb-sm">Status Variants</p>
                <div className="flex flex-wrap gap-xs">
                  <Chip variant="active">Active</Chip>
                  <Chip variant="pending">Pending</Chip>
                  <Chip variant="confirmed">Confirmed</Chip>
                  <Chip variant="alert">Alert</Chip>
                  <Chip variant="closed">Closed</Chip>
                </div>
              </div>
              
              <div>
                <p className="text-caption text-text-secondary mb-sm">Semantic Variants</p>
                <div className="flex flex-wrap gap-xs">
                  <Chip variant="info">Information</Chip>
                  <Chip variant="success">Success</Chip>
                  <Chip variant="warning">Warning</Chip>
                  <Chip variant="error">Error</Chip>
                </div>
              </div>
            </div>
          </Card>
        </section>

        {/* Tabs Section */}
        <section>
          <h2 className="text-display-md font-semibold text-text-primary mb-lg">Tabs & Segmented Controls</h2>
          <Card title="Navigation Tabs">
            <div className="space-y-lg">
              <div>
                <p className="text-caption text-text-secondary mb-sm">View Switcher</p>
                <Tabs tabs={['Overview', 'Analytics', 'Reports']} />
              </div>
              
              <div>
                <p className="text-caption text-text-secondary mb-sm">Time Period</p>
                <Tabs tabs={['Day', 'Week', 'Month', 'Year']} defaultTab={2} />
              </div>
            </div>
          </Card>
        </section>

        {/* Icons Section */}
        <section>
          <h2 className="text-display-md font-semibold text-text-primary mb-lg">Icons</h2>
          <Card title="Icon Library" subtitle="Simple, geometric line icons with 1.5px stroke weight">
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {[
                'menu', 'close', 'search', 'settings', 'user', 'users',
                'bell', 'heart', 'star', 'send', 'mail', 'chat',
                'attachment', 'image', 'camera', 'download', 'edit', 'trash',
                'copy', 'plus', 'minus', 'check', 'info', 'warning',
                'error', 'chevronDown', 'chevronUp', 'arrowLeft', 'arrowRight', 'moreVertical'
              ].map((iconName) => (
                <div key={iconName} className="flex flex-col items-center gap-2 p-3 rounded-lg hover:bg-surface-subtle transition-colors">
                  <div className="w-10 h-10 flex items-center justify-center text-text-primary">
                    <Icon name={iconName} size="lg" />
                  </div>
                  <span className="text-caption text-text-secondary text-center">{iconName}</span>
                </div>
              ))}
            </div>
          </Card>
        </section>

        {/* Modal & Overlays Section */}
        <section>
          <h2 className="text-display-md font-semibold text-text-primary mb-lg">Modal & Overlays</h2>
          <Card title="Modal Dialogs">
            <div className="space-y-md">
              <div>
                <p className="text-body text-text-secondary mb-4">
                  Modal dialogs for important actions, forms, and confirmations. Includes backdrop overlay, smooth animations, and keyboard support (ESC to close).
                </p>
                <Button variant="primary" onClick={() => setIsModalOpen(true)}>
                  Open Modal
                </Button>
              </div>
            </div>
          </Card>
          
          <Modal
            isOpen={isModalOpen}
            onClose={() => setIsModalOpen(false)}
            title="Create New Project"
            size="md"
            footer={
              <>
                <Button variant="secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button variant="primary" onClick={() => setIsModalOpen(false)}>
                  Create Project
                </Button>
              </>
            }
          >
            <div className="space-y-md">
              <Input 
                label="Project Name"
                placeholder="Enter project name"
              />
              <Input 
                label="Description"
                placeholder="Brief description of your project"
              />
              <Select
                label="Category"
                placeholder="Select category"
                options={[
                  { value: 'design', label: 'Design' },
                  { value: 'development', label: 'Development' },
                  { value: 'marketing', label: 'Marketing' },
                ]}
              />
            </div>
          </Modal>
        </section>

        {/* Forms & Inputs Section */}
        <section>
          <h2 className="text-display-md font-semibold text-text-primary mb-lg">Inputs & Forms</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-lg">
            <Card title="Text Inputs">
              <div className="space-y-md">
                <Input 
                  label="Email Address" 
                  placeholder="john@example.com"
                  helperText="We'll never share your email."
                />
                
                <Input 
                  label="Search" 
                  placeholder="Search for projects..."
                  icon={<Icon name="search" size="sm" />}
                />
                
                <Input 
                  label="Password" 
                  type="password"
                  placeholder="Enter password"
                  error="Password must be at least 8 characters"
                />
              </div>
            </Card>
            
            <Card title="Select & Dropdown">
              <div className="space-y-md">
                <Select
                  label="Country"
                  placeholder="Select your country"
                  options={[
                    { value: 'us', label: 'United States' },
                    { value: 'uk', label: 'United Kingdom' },
                    { value: 'ca', label: 'Canada' },
                    { value: 'au', label: 'Australia' },
                    { value: 'de', label: 'Germany' },
                  ]}
                  value={selectedCountry}
                  onChange={setSelectedCountry}
                />
                
                <Select
                  label="Language"
                  options={[
                    { value: 'en', label: 'English' },
                    { value: 'es', label: 'Spanish' },
                    { value: 'fr', label: 'French' },
                    { value: 'de', label: 'German' },
                  ]}
                  value="en"
                />
                
                <div>
                  <p className="text-caption text-text-secondary mb-2 font-medium">Actions Menu</p>
                  <Dropdown
                    trigger={
                      <Button variant="secondary">
                        Actions <Icon name="chevronDown" size="sm" className="ml-1" />
                      </Button>
                    }
                    items={[
                      { label: 'Edit', icon: <Icon name="edit" size="sm" />, onClick: () => console.log('Edit') },
                      { label: 'Duplicate', icon: <Icon name="copy" size="sm" />, onClick: () => console.log('Duplicate') },
                      { divider: true },
                      { label: 'Delete', icon: <Icon name="trash" size="sm" />, onClick: () => console.log('Delete'), danger: true },
                    ]}
                  />
                </div>
              </div>
            </Card>
          </div>
          
          <div className="mt-lg grid grid-cols-1 lg:grid-cols-2 gap-lg">
            <Card title="Tokenized Input">
              <div className="space-y-md">
                <TokenizedInput
                  label="Tags"
                  placeholder="Type and press Enter"
                  tokens={tokens}
                  onAddToken={(value) => setTokens([...tokens, { label: value }])}
                  onRemoveToken={(index) => setTokens(tokens.filter((_, i) => i !== index))}
                />
                
                <TokenizedInput
                  label="Team Members"
                  placeholder="Add team members"
                  showAvatar={true}
                  tokens={[
                    { label: 'John Doe', avatar: { fallback: 'JD' } },
                    { label: 'Alice Smith', avatar: { fallback: 'AS' } },
                  ]}
                />
              </div>
            </Card>
            
            <Card title="Toggle Switches">
              <div className="divide-y divide-border-subtle">
                <Toggle
                  label="Email Notifications"
                  description="Receive notifications via email"
                  checked={true}
                />
                
                <Toggle
                  label="Push Notifications"
                  description="Get push notifications on your device"
                  checked={false}
                />
                
                <Toggle
                  label="Marketing Emails"
                  description="Receive promotional emails and updates"
                  checked={true}
                />
              </div>
            </Card>
          </div>
        </section>

        {/* Banners & Notifications Section */}
        <section>
          <h2 className="text-display-md font-semibold text-text-primary mb-lg">Banners & Notifications</h2>
          <div className="space-y-md">
            <Banner 
              variant="info" 
              icon={<Icon name="info" size="md" />}
            >
              Your account has been successfully updated. Changes will take effect immediately.
            </Banner>
            
            <Banner 
              variant="success" 
              icon={<Icon name="check" size="md" />}
            >
              Payment processed successfully! Receipt has been sent to your email.
            </Banner>
            
            <Banner 
              variant="warning" 
              icon={<Icon name="warning" size="md" />}
            >
              Your subscription will expire in 7 days. Please renew to avoid service interruption.
            </Banner>
            
            <Banner 
              variant="error" 
              icon={<Icon name="error" size="md" />}
              onClose={() => console.log('Closed')}
            >
              Failed to save changes. Please check your connection and try again.
            </Banner>
          </div>
        </section>

        {/* Progress Bars Section */}
        <section>
          <h2 className="text-display-md font-semibold text-text-primary mb-lg">Progress & Metrics</h2>
          <Card title="Progress Indicators">
            <div className="space-y-lg">
              <ProgressBar 
                value={75} 
                label="Storage Used" 
                showLabel
                color="primary"
              />
              
              <ProgressBar 
                value={45} 
                label="Monthly Credits" 
                showLabel
                color="emerald"
              />
              
              <ProgressBar 
                value={90} 
                label="Bandwidth Usage" 
                showLabel
                color="orange"
              />
              
              <ProgressBar 
                value={95} 
                label="API Rate Limit" 
                showLabel
                color="red"
              />
            </div>
          </Card>
        </section>

        {/* Avatars Section */}
        <section>
          <h2 className="text-display-md font-semibold text-text-primary mb-lg">Avatars</h2>
          <Card title="User Avatars">
            <div className="space-y-lg">
              <div>
                <p className="text-caption text-text-secondary mb-sm">Avatar Sizes</p>
                <div className="flex items-center gap-md">
                  <Avatar size="sm" fallback="S" />
                  <Avatar size="md" fallback="M" />
                  <Avatar size="lg" fallback="L" />
                </div>
              </div>
              
              <div>
                <p className="text-caption text-text-secondary mb-sm">Avatar Group</p>
                <AvatarGroup 
                  avatars={[
                    { fallback: 'JD' },
                    { fallback: 'AS' },
                    { fallback: 'MK' },
                    { fallback: 'TL' },
                    { fallback: 'RP' },
                  ]}
                  max={3}
                  size="md"
                />
              </div>
            </div>
          </Card>
        </section>

        {/* Cards Section */}
        <section>
          <h2 className="text-display-md font-semibold text-text-primary mb-lg">Cards & Containers</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-lg">
            <Card 
              title="Active Conversations"
              subtitle="12 conversations in progress"
              actions={<Button variant="ghost">View All</Button>}
              footer={
                <div className="flex items-center justify-between">
                  <span className="text-caption text-text-secondary">Last updated 5 mins ago</span>
                  <Chip variant="active">Live</Chip>
                </div>
              }
            >
              <p className="text-body text-text-secondary">
                You have 12 active conversations with team members. 5 require your immediate attention.
              </p>
            </Card>
            
            <Card 
              title="Team Members"
              subtitle="8 members online"
              actions={<Button variant="tiny">+ Invite</Button>}
            >
              <AvatarGroup 
                avatars={[
                  { fallback: 'JD' },
                  { fallback: 'AS' },
                  { fallback: 'MK' },
                  { fallback: 'TL' },
                  { fallback: 'RP' },
                  { fallback: 'SK' },
                  { fallback: 'LM' },
                  { fallback: 'BC' },
                ]}
                max={5}
              />
            </Card>
          </div>
        </section>

        {/* List Items Section */}
        <section>
          <h2 className="text-display-md font-semibold text-text-primary mb-lg">List Items</h2>
          <Card title="Recent Activity">
            <div className="border border-border-subtle rounded-md overflow-hidden">
              <ListItem
                avatar={<Avatar fallback="JD" size="md" />}
                title="John Doe updated the project"
                subtitle="2 hours ago"
                status={<Chip variant="active">Active</Chip>}
              />
              
              <ListItem
                avatar={<Avatar fallback="AS" size="md" />}
                title="Alice Smith completed milestone"
                subtitle="5 hours ago"
                status={<Chip variant="confirmed">Done</Chip>}
              />
              
              <ListItem
                avatar={<Avatar fallback="MK" size="md" />}
                title="Mike Johnson requested review"
                subtitle="Yesterday"
                status={<Chip variant="pending">Pending</Chip>}
                actions={
                  <>
                    <Button variant="tiny">Review</Button>
                  </>
                }
              />
              
              <ListItem
                avatar={<Avatar fallback="SK" size="md" />}
                title="Sarah Kim left a comment"
                subtitle="2 days ago"
                status={<Chip variant="info">Comment</Chip>}
              />
            </div>
          </Card>
        </section>

        {/* Empty State Section */}
        <section>
          <h2 className="text-display-md font-semibold text-text-primary mb-lg">Empty States</h2>
          <EmptyState
            icon={<span className="text-6xl">📭</span>}
            title="No messages yet"
            description="When you start a conversation, your messages will appear here. Get started by reaching out to a team member."
            action={<Button variant="primary">Start Conversation</Button>}
          />
        </section>

        {/* Chat Box Section */}
        <section>
          <h2 className="text-display-md font-semibold text-text-primary mb-lg">Chat Box</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-lg">
            <ChatBox
              title="Team Discussion"
              participants={[
                { fallback: "AS" },
                { fallback: "MK" },
                { fallback: "TL" }
              ]}
              messages={chatMessages}
              onSendMessage={handleSendMessage}
              height="500px"
            />
            
            <ChatBox
              title="Customer Support"
              participants={[
                { fallback: "CS" }
              ]}
              messages={[]}
              onSendMessage={(msg) => console.log('Support message:', msg)}
              height="500px"
            />
          </div>
        </section>

        {/* Personal Center Preview */}
        <section>
          <h2 className="text-display-md font-semibold text-text-primary mb-lg">Personal Center</h2>
          <Card>
            <div className="text-center py-12">
              <span className="text-6xl mb-4 block">👤</span>
              <h3 className="text-subtitle font-semibold text-text-primary mb-2">
                User Profile & Settings
              </h3>
              <p className="text-body text-text-secondary mb-6 max-w-md mx-auto">
                Comprehensive user profile management with settings, activity tracking, and preferences.
              </p>
              <Button variant="primary" onClick={() => setCurrentView('personal-center')}>
                View Personal Center
              </Button>
            </div>
          </Card>
        </section>

      </div>
    </div>
  )
}

export default App

