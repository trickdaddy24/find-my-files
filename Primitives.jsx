/* global React */
const { useState } = React;

window.LX = {
  brandPurple: "#8A4DFF",
  brandPurpleHover: "#7A3DEF",
  brandBlue: "#2EC7FF",
  brandCyan: "#00E0FF",
  navy: "#0B0F2A",
};

function Icon({ name, size = 16, color, style }) {
  const s = { width: size, height: size, color, flexShrink: 0, ...style };
  return <i data-lucide={name} style={s} />;
}

function Button({ variant = "primary", dark, children, onClick, icon, disabled, fullWidth, small }) {
  const base = {
    padding: small ? "6px 14px" : "10px 22px",
    borderRadius: 8,
    fontSize: small ? 12 : 14,
    fontWeight: 500,
    border: 0,
    cursor: disabled ? "not-allowed" : "pointer",
    transition: "all .2s cubic-bezier(.4,0,.2,1)",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 7,
    width: fullWidth ? "100%" : undefined,
    opacity: disabled ? 0.5 : 1,
    fontFamily: "inherit",
  };
  const variantStyles = {
    primary: dark
      ? { ...base, background: "transparent", border: "2px solid #00E0FF", color: "#fff", boxShadow: "0 0 10px rgba(0,224,255,.5)" }
      : { ...base, background: "#8A4DFF", color: "#fff" },
    secondary: dark
      ? { ...base, background: "transparent", border: "1px solid rgba(0,224,255,.3)", color: "#94A3B8" }
      : { ...base, background: "transparent", border: "1px solid #E5E7EB", color: "#6B7280" },
    ghost: {
      ...base,
      background: "transparent",
      color: dark ? "#94A3B8" : "#6B7280",
    },
    danger: {
      ...base,
      background: dark ? "rgba(239,68,68,.15)" : "#FEF2F2",
      color: "#EF4444",
      border: "none",
    },
  };
  return (
    <button style={variantStyles[variant] || variantStyles.primary} onClick={onClick} disabled={disabled}>
      {icon ? <Icon name={icon} size={small ? 13 : 15} /> : null}
      {children}
    </button>
  );
}

function Input({ label, type = "text", value, onChange, placeholder, dark, right, style }) {
  const [focused, setFocused] = React.useState(false);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 5, ...style }}>
      {label && <label style={{ fontSize: 12, fontWeight: 500, color: dark ? "#CBD5E1" : "#374151" }}>{label}</label>}
      <div style={{ position: "relative" }}>
        <input
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          style={{
            width: "100%",
            padding: right ? "9px 36px 9px 12px" : "9px 12px",
            borderRadius: 8,
            fontSize: 13,
            fontFamily: "inherit",
            boxSizing: "border-box",
            outline: "none",
            background: dark ? "#1E293B" : "#F3F4F6",
            border: `1px solid ${focused ? "transparent" : dark ? "#334155" : "#D1D5DB"}`,
            color: dark ? "#F1F5F9" : "#0B0F2A",
            boxShadow: focused ? "0 0 0 2px #8A4DFF" : "none",
            transition: "box-shadow .15s, border-color .15s",
          }}
        />
        {right && (
          <div style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", color: dark ? "#64748B" : "#9CA3AF" }}>
            {right}
          </div>
        )}
      </div>
    </div>
  );
}

Object.assign(window, { Icon, Button, Input, LX });
