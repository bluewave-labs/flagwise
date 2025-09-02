# FlagWise Design System Implementation Guide

This document contains everything needed to implement the FlagWise design system in a new React project.

## Overview

The FlagWise design system is built on:
- **Tailwind CSS** with custom design tokens
- **Radix UI** primitives for accessibility
- **Class Variance Authority (CVA)** for component variants
- **HSL-based color system** with dark mode support

## 1. Dependencies Installation

First, install the required dependencies:

```bash
npm install @radix-ui/react-avatar @radix-ui/react-checkbox @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-label @radix-ui/react-select @radix-ui/react-slot @radix-ui/react-switch @radix-ui/react-tabs @radix-ui/react-toast class-variance-authority clsx lucide-react tailwind-merge tailwindcss-animate

npm install -D tailwindcss postcss autoprefixer
```

## 2. Tailwind Configuration

Create or update your `tailwind.config.js`:

```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{js,jsx}',
    './components/**/*.{js,jsx}',
    './app/**/*.{js,jsx}',
    './src/**/*.{js,jsx}',
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        DEFAULT: "4px",
        lg: "4px",
        md: "4px", 
        sm: "4px",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

## 3. Global Styles

Create or update your main CSS file (e.g., `src/index.css` or `src/globals.css`):

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96%;
    --secondary-foreground: 222.2 84% 4.9%;
    --muted: 210 40% 96%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96%;
    --accent-foreground: 222.2 84% 4.9%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.25rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
  
  /* Custom heading styles - Override any inline classes */
  h1 {
    @apply text-xl font-normal text-muted-foreground !important;
  }
  
  h2 {
    @apply text-lg font-normal text-muted-foreground !important;
  }
  
  /* Enhanced Metric Card Styles */
  .metric-card-enhanced {
    position: relative;
  }
  
  .metric-card-enhanced::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: 
      linear-gradient(90deg, rgba(0, 0, 0, 0.02) 1px, transparent 1px),
      linear-gradient(180deg, rgba(0, 0, 0, 0.02) 1px, transparent 1px);
    background-size: 20px 20px;
    pointer-events: none;
    z-index: 1;
  }
  
  .metric-card-enhanced::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
      radial-gradient(ellipse at top left, rgba(0, 0, 0, 0.02) 0%, transparent 50%),
      radial-gradient(ellipse at top right, rgba(0, 0, 0, 0.02) 0%, transparent 50%),
      radial-gradient(ellipse at bottom left, rgba(0, 0, 0, 0.015) 0%, transparent 50%),
      radial-gradient(ellipse at bottom right, rgba(0, 0, 0, 0.015) 0%, transparent 50%);
    pointer-events: none;
    z-index: 2;
  }
  
  .metric-card-enhanced > * {
    position: relative;
    z-index: 3;
  }
}
```

## 4. Utility Functions

Create `src/lib/utils.js`:

```js
import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

export function getErrorMessage(error, fallback = 'An error occurred') {
  if (error?.response?.data?.detail) {
    const detail = error.response.data.detail;
    
    if (typeof detail === 'string') {
      return detail;
    } else if (Array.isArray(detail)) {
      // Handle Pydantic validation errors with field mapping
      return detail.map(err => {
        const fieldName = err.loc && err.loc.length > 0 ? err.loc[err.loc.length - 1] : 'field';
        const fieldLabel = getFieldLabel(fieldName);
        const enhancedMessage = enhanceErrorMessage(fieldName, err.msg, err.type);
        return `${fieldLabel}: ${enhancedMessage}`;
      }).join('; ');
    } else {
      return 'Validation error occurred';
    }
  }
  
  return fallback;
}

function getFieldLabel(fieldName) {
  const fieldLabels = {
    'username': 'Username',
    'password': 'Password',
    'first_name': 'First Name',
    'last_name': 'Last Name',
    'role': 'Role',
    'is_active': 'Status',
    'current_password': 'Current Password',
    'new_password': 'New Password',
    'confirm_password': 'Confirm Password'
  };
  
  return fieldLabels[fieldName] || fieldName.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function enhanceErrorMessage(fieldName, message, errorType) {
  // Enhanced field-specific error messages
  const fieldSpecificMessages = {
    username: {
      'too_short': 'must be at least 3 characters long',
      'too_long': 'must be no more than 50 characters long',
      'string_pattern_mismatch': 'can only contain letters, numbers, hyphens, and underscores',
      'missing': 'is required'
    },
    password: {
      'too_short': 'must be at least 6 characters long',
      'missing': 'is required'
    },
    new_password: {
      'too_short': 'must be at least 6 characters long',
      'missing': 'is required'
    },
    current_password: {
      'missing': 'is required'
    },
    first_name: {
      'too_long': 'is too long'
    },
    last_name: {
      'too_long': 'is too long'
    }
  };

  // Check for field-specific enhanced messages
  if (fieldSpecificMessages[fieldName] && fieldSpecificMessages[fieldName][errorType]) {
    return fieldSpecificMessages[fieldName][errorType];
  }

  // Check for generic error type enhancements
  if (errorType === 'missing') {
    return 'is required';
  } else if (errorType === 'too_short') {
    return message.toLowerCase();
  } else if (errorType === 'too_long') {
    return message.toLowerCase();
  } else if (errorType === 'string_pattern_mismatch') {
    if (fieldName === 'username') {
      return 'can only contain letters, numbers, hyphens, and underscores';
    }
    return 'format is invalid';
  }

  // Return original message if no enhancement available
  return message.toLowerCase();
}
```

## 5. Core UI Components

Create the following components in `src/components/ui/`:

### Button Component (`src/components/ui/button.jsx`)

```jsx
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority"
import { cn } from "../../lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded text-[13px] ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-[34px] font-normal",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline:
          "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "px-4 py-2",
        sm: "rounded px-3",
        lg: "rounded px-8",
        icon: "w-[34px]",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

const Button = React.forwardRef(({ className, variant, size, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button"
  return (
    <Comp
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      {...props}
    />
  )
})
Button.displayName = "Button"

export { Button, buttonVariants }
```

### Card Component (`src/components/ui/card.jsx`)

```jsx
import * as React from "react"
import { cn } from "../../lib/utils"

const Card = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded border bg-card text-card-foreground shadow-sm",
      className
    )}
    {...props}
  />
))
Card.displayName = "Card"

const CardHeader = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
))
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "text-lg font-normal leading-none tracking-tight text-muted-foreground",
      className
    )}
    {...props}
  />
))
CardTitle.displayName = "CardTitle"

const CardDescription = React.forwardRef(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-[13px] text-muted-foreground", className)}
    {...props}
  />
))
CardDescription.displayName = "CardDescription"

const CardContent = React.forwardRef(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
))
CardContent.displayName = "CardContent"

const CardFooter = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
))
CardFooter.displayName = "CardFooter"

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }
```

### Badge Component (`src/components/ui/badge.jsx`)

```jsx
import * as React from "react"
import { cva } from "class-variance-authority"
import { cn } from "../../lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded border px-2.5 py-0.5 text-xs font-normal transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({ className, variant, ...props }) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
```

### Input Component (`src/components/ui/input.jsx`)

```jsx
import * as React from "react"
import { cn } from "../../lib/utils"

const Input = React.forwardRef(({ className, type, ...props }, ref) => {
  return (
    <input
      type={type}
      className={cn(
        "flex h-9 w-full rounded border border-input bg-background px-3 py-2 text-[13px] ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      ref={ref}
      {...props}
    />
  )
})
Input.displayName = "Input"

export { Input }
```

### Alert Component (`src/components/ui/alert.jsx`)

```jsx
import * as React from "react"
import { cva } from "class-variance-authority"
import { cn } from "../../lib/utils"

const alertVariants = cva(
  "relative w-full rounded border p-4 [&>svg~*]:pl-7 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground",
  {
    variants: {
      variant: {
        default: "bg-background text-foreground",
        destructive:
          "border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

const Alert = React.forwardRef(({ className, variant, ...props }, ref) => (
  <div
    ref={ref}
    role="alert"
    className={cn(alertVariants({ variant }), className)}
    {...props}
  />
))
Alert.displayName = "Alert"

const AlertTitle = React.forwardRef(({ className, ...props }, ref) => (
  <h5
    ref={ref}
    className={cn("mb-1 font-medium leading-none tracking-tight", className)}
    {...props}
  />
))
AlertTitle.displayName = "AlertTitle"

const AlertDescription = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("text-[13px] [&_p]:leading-relaxed", className)}
    {...props}
  />
))
AlertDescription.displayName = "AlertDescription"

export { Alert, AlertTitle, AlertDescription }
```

### Label Component (`src/components/ui/label.jsx`)

```jsx
import * as React from "react"
import * as LabelPrimitive from "@radix-ui/react-label"
import { cva } from "class-variance-authority"
import { cn } from "../../lib/utils"

const labelVariants = cva(
  "text-[13px] font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
)

const Label = React.forwardRef(({ className, ...props }, ref) => (
  <LabelPrimitive.Root
    ref={ref}
    className={cn(labelVariants(), className)}
    {...props}
  />
))
Label.displayName = LabelPrimitive.Root.displayName

export { Label }
```

## 6. Advanced Components

### Select Component (`src/components/ui/select.jsx`)

```jsx
import * as React from "react"
import * as SelectPrimitive from "@radix-ui/react-select"
import { Check, ChevronDown, ChevronUp } from "lucide-react"
import { cn } from "../../lib/utils"

const Select = SelectPrimitive.Root
const SelectGroup = SelectPrimitive.Group
const SelectValue = SelectPrimitive.Value

const SelectTrigger = React.forwardRef(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Trigger
    ref={ref}
    className={cn(
      "flex h-9 w-full items-center justify-between rounded border border-input bg-background px-3 py-2 text-[13px] ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 [&>span]:line-clamp-1",
      className
    )}
    {...props}
  >
    {children}
    <SelectPrimitive.Icon asChild>
      <ChevronDown className="h-4 w-4 opacity-50" />
    </SelectPrimitive.Icon>
  </SelectPrimitive.Trigger>
))
SelectTrigger.displayName = SelectPrimitive.Trigger.displayName

const SelectScrollUpButton = React.forwardRef(({ className, ...props }, ref) => (
  <SelectPrimitive.ScrollUpButton
    ref={ref}
    className={cn("flex cursor-default items-center justify-center py-1", className)}
    {...props}
  >
    <ChevronUp className="h-4 w-4" />
  </SelectPrimitive.ScrollUpButton>
))
SelectScrollUpButton.displayName = SelectPrimitive.ScrollUpButton.displayName

const SelectScrollDownButton = React.forwardRef(({ className, ...props }, ref) => (
  <SelectPrimitive.ScrollDownButton
    ref={ref}
    className={cn("flex cursor-default items-center justify-center py-1", className)}
    {...props}
  >
    <ChevronDown className="h-4 w-4" />
  </SelectPrimitive.ScrollDownButton>
))
SelectScrollDownButton.displayName = SelectPrimitive.ScrollDownButton.displayName

const SelectContent = React.forwardRef(({ className, children, position = "popper", ...props }, ref) => (
  <SelectPrimitive.Portal>
    <SelectPrimitive.Content
      ref={ref}
      className={cn(
        "relative z-50 max-h-96 min-w-[8rem] overflow-hidden rounded border bg-popover text-popover-foreground shadow-md data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
        position === "popper" &&
          "data-[side=bottom]:translate-y-1 data-[side=left]:-translate-x-1 data-[side=right]:translate-x-1 data-[side=top]:-translate-y-1",
        className
      )}
      position={position}
      {...props}
    >
      <SelectScrollUpButton />
      <SelectPrimitive.Viewport
        className={cn(
          "p-1",
          position === "popper" &&
            "h-[var(--radix-select-trigger-height)] w-full min-w-[var(--radix-select-trigger-width)]"
        )}
      >
        {children}
      </SelectPrimitive.Viewport>
      <SelectScrollDownButton />
    </SelectPrimitive.Content>
  </SelectPrimitive.Portal>
))
SelectContent.displayName = SelectPrimitive.Content.displayName

const SelectLabel = React.forwardRef(({ className, ...props }, ref) => (
  <SelectPrimitive.Label
    ref={ref}
    className={cn("py-1.5 pl-8 pr-2 text-[13px] font-semibold", className)}
    {...props}
  />
))
SelectLabel.displayName = SelectPrimitive.Label.displayName

const SelectItem = React.forwardRef(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Item
    ref={ref}
    className={cn(
      "relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-[13px] outline-none focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
      className
    )}
    {...props}
  >
    <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
      <SelectPrimitive.ItemIndicator>
        <Check className="h-4 w-4" />
      </SelectPrimitive.ItemIndicator>
    </span>

    <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
  </SelectPrimitive.Item>
))
SelectItem.displayName = SelectPrimitive.Item.displayName

const SelectSeparator = React.forwardRef(({ className, ...props }, ref) => (
  <SelectPrimitive.Separator
    ref={ref}
    className={cn("-mx-1 my-1 h-px bg-muted", className)}
    {...props}
  />
))
SelectSeparator.displayName = SelectPrimitive.Separator.displayName

export {
  Select,
  SelectGroup,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectLabel,
  SelectItem,
  SelectSeparator,
  SelectScrollUpButton,
  SelectScrollDownButton,
}
```

### Metric Card Component (`src/components/ui/metric-card.jsx`)

```jsx
import * as React from "react"
import { cn } from "../../lib/utils"

const MetricCard = React.forwardRef(({ className, variant, ...props }, ref) => {
  const variants = {
    blue: "border-l-4 border-l-blue-500 bg-blue-50/50 hover:bg-blue-50/70",
    red: "border-l-4 border-l-red-500 bg-red-50/50 hover:bg-red-50/70",
    green: "border-l-4 border-l-green-500 bg-green-50/50 hover:bg-green-50/70",
    orange: "border-l-4 border-l-orange-500 bg-orange-50/50 hover:bg-orange-50/70",
    purple: "border-l-4 border-l-purple-500 bg-purple-50/50 hover:bg-purple-50/70",
    default: "border-l-4 border-l-gray-500 bg-gray-50/50 hover:bg-gray-50/70"
  }

  return (
    <div
      ref={ref}
      className={cn(
        "rounded border bg-card text-card-foreground shadow-sm transition-colors",
        variant && variants[variant],
        "metric-card-enhanced",
        className
      )}
      {...props}
    />
  )
})
MetricCard.displayName = "MetricCard"

const MetricCardContent = React.forwardRef(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6", className)} {...props} />
))
MetricCardContent.displayName = "MetricCardContent"

export { MetricCard, MetricCardContent }
```

## 7. Component Exports

Create `src/components/ui/index.js`:

```js
export { Button, buttonVariants } from './button'
export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent } from './card'
export { Badge, badgeVariants } from './badge'
export { Input } from './input'
export { Alert, AlertTitle, AlertDescription } from './alert'
export { Label } from './label'
export {
  Select,
  SelectGroup,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectLabel,
  SelectItem,
  SelectSeparator,
} from './select'
export { MetricCard, MetricCardContent } from './metric-card'
```

## 8. Usage Examples

### Basic Usage

```jsx
import React from 'react'
import { Button, Card, CardHeader, CardTitle, CardContent, Badge, Input, Label } from './components/ui'

function App() {
  return (
    <div className="p-8 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Welcome to FlagWise Design System</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Button variant="default">Primary Button</Button>
            <Button variant="outline">Secondary Button</Button>
            <Button variant="destructive">Delete</Button>
          </div>
          
          <div className="flex gap-2">
            <Badge variant="default">Status</Badge>
            <Badge variant="secondary">Info</Badge>
            <Badge variant="destructive">Error</Badge>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" placeholder="Enter your email" />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default App
```

### Advanced Layout Example

```jsx
import React from 'react'
import { Card, CardHeader, CardTitle, CardContent, MetricCard, MetricCardContent, Badge } from './components/ui'
import { Activity, Shield, Zap } from 'lucide-react'

function Dashboard() {
  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      
      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard variant="blue">
          <MetricCardContent>
            <div className="flex items-center">
              <Activity className="h-5 w-5 text-blue-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-muted-foreground">Total Requests</p>
                <p className="text-xl font-medium text-gray-700">1,234</p>
              </div>
            </div>
          </MetricCardContent>
        </MetricCard>
        
        <MetricCard variant="red">
          <MetricCardContent>
            <div className="flex items-center">
              <Shield className="h-5 w-5 text-red-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-muted-foreground">Threats Detected</p>
                <div className="flex items-center">
                  <p className="text-xl font-medium text-gray-700">5.2%</p>
                  <Badge variant="destructive" className="ml-2">64 flagged</Badge>
                </div>
              </div>
            </div>
          </MetricCardContent>
        </MetricCard>
        
        <MetricCard variant="orange">
          <MetricCardContent>
            <div className="flex items-center">
              <Zap className="h-5 w-5 text-orange-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-muted-foreground">Avg Response Time</p>
                <p className="text-xl font-medium text-gray-700">245ms</p>
              </div>
            </div>
          </MetricCardContent>
        </MetricCard>
      </div>
    </div>
  )
}

export default Dashboard
```

## 9. Design Tokens Reference

### Typography
- **Base font size**: 13px (`text-[13px]`)
- **Headings**: Normal font weight (`font-normal`)
- **Button text**: 13px (`text-[13px]`)

### Spacing
- **Button height**: 34px (`h-[34px]`)
- **Card padding**: 24px (`p-6`)
- **Input height**: 36px (`h-9`)

### Colors
- **Primary**: Dark blue-gray (`hsl(222.2 47.4% 11.2%)`)
- **Secondary**: Light gray (`hsl(210 40% 96%)`)
- **Destructive**: Red (`hsl(0 84.2% 60.2%)`)
- **Muted**: Subtle gray text (`hsl(215.4 16.3% 46.9%)`)

### Border Radius
- **Consistent**: 4px for all components

## 10. Dark Mode

The design system includes built-in dark mode support. Toggle with:

```jsx
// Add to your root component or layout
<html className="dark"> // or remove for light mode
```

## 11. Implementation Checklist

- [ ] Install all required dependencies
- [ ] Update tailwind.config.js with FlagWise configuration
- [ ] Add global styles to CSS file
- [ ] Create utils.js with cn function
- [ ] Add all UI components to components/ui/
- [ ] Create component index file for exports
- [ ] Test basic components (Button, Card, Badge)
- [ ] Implement metric cards for enhanced layouts
- [ ] Test dark mode functionality
- [ ] Verify consistent 13px font sizing throughout

## 12. Additional Components

If you need more components, follow the established patterns:
- Use CVA for variants
- Apply consistent spacing (p-6, h-9, etc.)
- Use semantic color tokens
- Include proper TypeScript types
- Follow Radix UI patterns for accessibility

The design system is now ready for implementation in your new project!