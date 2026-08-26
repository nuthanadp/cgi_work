// src/components/ToggleSwitch.jsx

import React from 'react';

/**
 * A simple, modern toggle switch component.
 *
 * Props:
 * - isToggled: (boolean) Whether the switch is on or off.
 * - onToggle: (function) The callback function to run when clicked.
 * - disabled: (boolean) Optional. Disables the switch.
 */
const ToggleSwitch = ({ isToggled, onToggle, disabled = false }) => {
  return (
    <label className="toggle-switch" htmlFor={`toggle-${Math.random()}`}>
      <input
        type="checkbox"
        id={`toggle-${Math.random()}`}
        checked={isToggled}
        onChange={onToggle}
        disabled={disabled}
      />
      <span className="slider round"></span>
    </label>
  );
};

export default ToggleSwitch;