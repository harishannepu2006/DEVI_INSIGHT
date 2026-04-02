import React from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { HiOutlineMoon, HiOutlineSun } from 'react-icons/hi';

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button 
      onClick={toggleTheme} 
      className="nav-link" 
      style={{ marginTop: 'auto', display: 'flex', alignItems: 'center', gap: '12px' }}
      title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
    >
      <span className="nav-icon">
        {theme === 'dark' ? <HiOutlineSun /> : <HiOutlineMoon />}
      </span>
      {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
    </button>
  );
}
