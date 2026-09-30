export default function FormField({
  label,
  name,
  type = "text",
  value,
  onChange,
  required = false,
  placeholder = "",
  children,
  min,
  max,
  maxLength,
  pattern,
  help,
}) {
  return (
    <label className="field">
      <span className="field-label">
        {label}
        {required ? <span className="required"> *</span> : null}
      </span>

      {children || (
        <input
          name={name}
          type={type}
          value={value ?? ""}
          onChange={onChange}
          required={required}
          placeholder={placeholder}
          min={min}
          max={max}
          maxLength={maxLength}
          pattern={pattern}
        />
      )}

      {help ? <span className="field-help">{help}</span> : null}
    </label>
  );
}
