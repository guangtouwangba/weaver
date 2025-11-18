import React, { useState } from 'react'
import Avatar from './Avatar'
import Button from './Button'
import Chip from './Chip'

export const ChatMessage = ({ 
  message, 
  sender, 
  timestamp, 
  isOwn = false,
  avatar,
  status
}) => {
  return (
    <div className={`flex gap-3 mb-4 ${isOwn ? 'flex-row-reverse' : 'flex-row'}`}>
      <div className="flex-shrink-0 pt-1">
        <Avatar {...avatar} size="md" />
      </div>
      
      <div className={`flex-1 max-w-[70%] ${isOwn ? 'items-end' : 'items-start'} flex flex-col`}>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-caption font-medium text-text-primary">{sender}</span>
          <span className="text-caption text-text-muted">{timestamp}</span>
          {status && <Chip variant={status.variant}>{status.label}</Chip>}
        </div>
        
        <div className={`
          px-4 py-3 rounded-lg text-body
          ${isOwn 
            ? 'bg-primary-strong text-text-on-accent rounded-tr-sm' 
            : 'bg-surface-subtle text-text-primary rounded-tl-sm'
          }
        `}>
          {message}
        </div>
      </div>
    </div>
  )
}

export const ChatBox = ({ 
  title = "Conversation",
  participants = [],
  messages = [],
  onSendMessage,
  placeholder = "Type a message...",
  height = "600px",
  ...props 
}) => {
  const [inputValue, setInputValue] = useState('')

  const handleSend = () => {
    if (inputValue.trim()) {
      onSendMessage?.(inputValue)
      setInputValue('')
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="bg-surface-card rounded-lg shadow-soft overflow-hidden flex flex-col" style={{ height }} {...props}>
      {/* Header */}
      <div className="px-5 py-4 border-b border-border-subtle bg-surface-card">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h3 className="text-subtitle font-semibold text-text-primary">{title}</h3>
            {participants.length > 0 && (
              <div className="flex -space-x-2">
                {participants.slice(0, 3).map((participant, index) => (
                  <div key={index} className="ring-2 ring-surface-card rounded-full">
                    <Avatar {...participant} size="sm" />
                  </div>
                ))}
                {participants.length > 3 && (
                  <div className="w-6 h-6 rounded-full bg-surface-subtle ring-2 ring-surface-card flex items-center justify-center text-[10px] text-text-secondary font-semibold">
                    +{participants.length - 3}
                  </div>
                )}
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <Chip variant="active">Online</Chip>
            <button 
              className="w-8 h-8 flex items-center justify-center rounded-lg text-text-secondary hover:bg-surface-subtle active:bg-surface-page transition-all"
              title="More options"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-5 py-4 bg-surface-page">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <span className="text-4xl mb-3">💬</span>
            <p className="text-body text-text-secondary">No messages yet</p>
            <p className="text-caption text-text-muted mt-1">Start the conversation!</p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <ChatMessage key={index} {...msg} />
          ))
        )}
      </div>

      {/* Input Area */}
      <div className="px-5 py-4 border-t border-border-subtle bg-surface-card">
        <div className="flex gap-2 items-start">
          {/* Attachment Button */}
          <button 
            className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-lg text-text-secondary hover:bg-surface-subtle active:bg-surface-page transition-all"
            title="Attach file"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
            </svg>
          </button>
          
          {/* Input Container */}
          <div className="flex-1 flex items-start gap-2 px-3 py-2 bg-surface-subtle border border-border-subtle rounded-xl focus-within:border-border-focus focus-within:ring-2 focus-within:ring-primary-soft transition-all duration-normal ease-standard">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={placeholder}
              rows={1}
              className="flex-1 bg-transparent text-body resize-none outline-none placeholder:text-text-muted min-h-[24px] max-h-[120px]"
              style={{ lineHeight: '1.5' }}
            />
            
            {/* Emoji Button - Inside Input */}
            <button 
              className="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded hover:bg-surface-card transition-all text-lg"
              title="Add emoji"
            >
              😊
            </button>
          </div>
          
          {/* Send Button */}
          <Button 
            variant="primary" 
            onClick={handleSend}
            disabled={!inputValue.trim()}
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
            Send
          </Button>
        </div>
        
        <div className="flex items-center justify-between mt-2">
          <span className="text-caption text-text-muted">
            Press Enter to send, Shift + Enter for new line
          </span>
          <span className="text-caption text-text-muted">
            {inputValue.length > 0 && `${inputValue.length} characters`}
          </span>
        </div>
      </div>
    </div>
  )
}

export default ChatBox

