# Design System Components

This document describes the new system components built following the design.json specification.

## ChatBox Component

A fully-featured messaging interface for real-time conversations.

### Features
- **Message bubbles** with sender avatars and timestamps
- **Own vs received messages** with different styling (blue for own, gray for received)
- **Participant indicators** showing who's in the conversation
- **Status indicators** (Online/Offline)
- **Rich input area** with attachment and emoji buttons
- **Empty state** for new conversations
- **Auto-scroll** behavior for new messages

### Props
- `title` (string): Conversation title
- `participants` (array): List of participant objects with avatar data
- `messages` (array): Array of message objects
- `onSendMessage` (function): Callback when sending a message
- `placeholder` (string): Input placeholder text
- `height` (string): Container height (default: "600px")

### Message Object Structure
```javascript
{
  message: "Message text",
  sender: "Sender Name",
  timestamp: "10:30 AM",
  isOwn: false, // true for user's own messages
  avatar: { fallback: "AS" },
  status: { variant: "active", label: "Active" } // optional
}
```

### Usage Example
```jsx
<ChatBox
  title="Team Discussion"
  participants={[
    { fallback: "AS" },
    { fallback: "MK" }
  ]}
  messages={messages}
  onSendMessage={(msg) => handleNewMessage(msg)}
  height="500px"
/>
```

## PersonalCenter Component

A comprehensive user profile and settings management interface.

### Features
- **Profile Header** with avatar, stats, and quick actions
- **Tabbed Navigation** (Profile, Settings, Activity, Preferences)
- **Editable Profile** with edit mode toggle
- **Account Progress** indicators (profile completion, storage)
- **Privacy Settings** with toggle switches
- **Notification Preferences**
- **Appearance Settings** (theme, language)
- **Activity Timeline** showing recent actions
- **Danger Zone** for account deletion

### Tabs

#### 1. Profile Tab
- Personal information form (name, email, phone)
- Bio/description textarea
- Profile completion progress
- Storage usage indicator
- Edit mode with save/cancel

#### 2. Settings Tab
- Account settings (username, password)
- Privacy toggles (profile visibility, email display, activity status)
- Danger zone with destructive actions

#### 3. Activity Tab
- Timeline of recent user actions
- Status indicators for each activity
- Empty state when no activity

#### 4. Preferences Tab
- Notification preferences (email, push, SMS)
- Appearance settings (theme selection)
- Language selector

### Props
- `user` (object): User data object
- `stats` (object): User statistics
- `activities` (array): Recent activity items
- `settings` (object): User settings
- `onUpdateProfile` (function): Profile update callback
- `onUpdateSettings` (function): Settings update callback

### User Object Structure
```javascript
{
  name: "John Doe",
  email: "john@example.com",
  firstName: "John",
  lastName: "Doe",
  username: "johndoe",
  role: "Admin",
  phone: "+1 (555) 123-4567",
  bio: "User bio text",
  avatar: "/path/to/avatar.jpg" // optional
}
```

### Stats Object Structure
```javascript
{
  projects: 24,
  conversations: 156,
  contributions: 892,
  followers: 1240
}
```

### Usage Example
```jsx
<PersonalCenter 
  user={userData}
  stats={userStats}
  activities={recentActivities}
  onUpdateProfile={(data) => handleProfileUpdate(data)}
  onUpdateSettings={(data) => handleSettingsUpdate(data)}
/>
```

## Design System Compliance

Both components follow the design.json specifications:

### Colors
- Uses semantic color tokens (primary, emerald, orange, red)
- Proper text contrast ratios
- Consistent status color mapping

### Typography
- Follows type scale (display-md, subtitle, body, caption, label)
- Proper font weights and line heights
- Consistent text hierarchy

### Spacing
- Uses spacing scale (xs, sm, md, lg, xl)
- Consistent padding and margins
- Proper component spacing

### Components
- Rounded corners (lg for cards, pill for buttons/chips)
- Soft shadows for elevation
- Proper border styles and colors
- Interactive states (hover, active, focus, disabled)

### Accessibility
- Keyboard navigation support
- Focus indicators
- WCAG AA contrast compliance
- Proper ARIA labels (to be added)
- Screen reader friendly structure

## Interactive Elements

### ChatBox
- Click to send messages
- Enter key to send (Shift+Enter for new line)
- Attachment button (placeholder)
- Emoji picker button (placeholder)
- More options menu (placeholder)

### PersonalCenter
- Toggle switches for privacy/notification settings
- Tab navigation
- Edit mode toggle
- File upload for avatar (visual only)
- Form validation (to be implemented)
- Save/cancel actions

## Future Enhancements

### ChatBox
- [ ] File upload/attachment handling
- [ ] Emoji picker integration
- [ ] Message reactions
- [ ] Read receipts
- [ ] Typing indicators
- [ ] Message search
- [ ] Voice messages
- [ ] Video call integration

### PersonalCenter
- [ ] Two-factor authentication setup
- [ ] Connected accounts
- [ ] Billing/subscription management
- [ ] Export user data
- [ ] Account deletion flow
- [ ] Profile badge/verification
- [ ] Social media links
- [ ] Custom theme colors

