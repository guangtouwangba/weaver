import React, { useState } from 'react'

export const Tabs = ({ tabs, defaultTab = 0, onChange }) => {
  const [activeTab, setActiveTab] = useState(defaultTab)

  const handleTabClick = (index) => {
    setActiveTab(index)
    if (onChange) onChange(index)
  }

  return (
    <div className="inline-flex gap-2 bg-surface-subtle rounded-pill p-1">
      {tabs.map((tab, index) => (
        <button
          key={index}
          onClick={() => handleTabClick(index)}
          className={`
            px-[14px] h-8 rounded-pill text-label font-label transition-all duration-180
            ${activeTab === index 
              ? 'bg-primary-strong text-text-on-accent' 
              : 'bg-transparent text-text-secondary hover:bg-surface-card'
            }
          `}
        >
          {tab}
        </button>
      ))}
    </div>
  )
}

export default Tabs

