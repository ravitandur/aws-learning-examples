import React from 'react';
import { cn } from "../../shared/utils/cn";

interface ToggleProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isPressed?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const Toggle = React.forwardRef<HTMLButtonElement, ToggleProps>(
  ({ className, isPressed, size = 'md', ...props }, ref) => {
    const sizes = {
      sm: "h-8 px-2.5",
      md: "h-10 px-3",
      lg: "h-12 px-5",
    };

    return (
      <button
        ref={ref}
        aria-pressed={isPressed}
        data-state={isPressed ? "on" : "off"}
        className={cn(
          "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors hover:bg-gray-100 hover:text-gray-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 dark:hover:bg-gray-800 dark:hover:text-gray-50",
          isPressed && "bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-50",
          sizes[size],
          className
        )}
        {...props}
      />
    );
  }
);

Toggle.displayName = "Toggle";

export default Toggle;