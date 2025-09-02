# Frontend - CLAUDE.md

This file provides specific guidance for frontend development in the Quantleap Analytics trading platform.

## Current Environment Configuration (September 2, 2025)

### ✅ Multi-API Architecture Deployment
**Status**: ✅ Updated with both deployed stack endpoints

#### **API Endpoints**:
- **User Authentication & Broker Management**: `https://4fhetaydtg.execute-api.ap-south-1.amazonaws.com/dev/`
- **Options Trading Platform**: `https://2f8bmi4edb.execute-api.ap-south-1.amazonaws.com/dev/`

#### **Environment Variables** (`.env`):
```env
REACT_APP_ENVIRONMENT=dev
REACT_APP_API_URL_DEV=https://4fhetaydtg.execute-api.ap-south-1.amazonaws.com/dev
REACT_APP_OPTIONS_API_URL_DEV=https://2f8bmi4edb.execute-api.ap-south-1.amazonaws.com/dev
REACT_APP_DEBUG=true
REACT_APP_AUTH_STACK_NAME=ql-algo-trading-dev-auth-broker-stack
REACT_APP_OPTIONS_STACK_NAME=ql-algo-trading-dev-options-trading-stack
```

#### **Development Status**:
- **Frontend Server**: Running at `http://localhost:3000`
- **Hot Reload**: Active with updated environment variables
- **TypeScript**: Clean compilation with comprehensive type safety
- **API Integration**: Dual API architecture configured and ready

## Development Standards

### Layout Pattern (MANDATORY)
All React pages MUST follow this exact pattern for consistency:

```tsx
const PageComponent: React.FC = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Page Title</h1>
      
      {/* Content sections with consistent spacing */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Stat cards or content blocks */}
      </div>
      
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          {/* Header section */}
        </div>
        <div className="p-6">
          {/* Main content */}
        </div>
      </div>
    </div>
  );
};
```

### Critical Layout Rules
1. **Root Container**: ALWAYS use `<div className="space-y-6">` - never add width constraints
2. **Page Titles**: ALWAYS use `text-2xl font-bold` - never text-3xl
3. **Section Spacing**: Use `space-y-6` between major sections
4. **Cards**: Use `bg-white dark:bg-gray-800 rounded-lg shadow`
5. **No Width Constraints**: Layout component handles responsive padding

### Design System Components

#### Typography
- **Page Headers**: `text-2xl font-bold text-gray-900 dark:text-white`
- **Section Headers**: `text-lg font-semibold text-gray-900 dark:text-white`
- **Body Text**: `text-gray-600 dark:text-gray-300`
- **Labels**: `text-sm font-medium text-gray-700 dark:text-gray-200`

#### Form Elements
- **Input Background**: `bg-white dark:bg-gray-700`
- **Input Borders**: `border-gray-300 dark:border-gray-600`
- **Input Text**: `text-gray-900 dark:text-white`
- **Placeholders**: `placeholder-gray-500 dark:placeholder-gray-400`
- **Focus States**: `focus:ring-2 focus:ring-blue-500 focus:border-blue-500`

#### Interactive Elements
- **Primary Buttons**: `bg-blue-600 hover:bg-blue-700 text-white`
- **Links**: `text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300`
- **Disabled States**: `disabled:bg-blue-300 dark:disabled:bg-blue-800`

#### Cards and Containers
- **Card Background**: `bg-white dark:bg-gray-800`
- **Card Borders**: `border border-gray-200 dark:border-gray-700`
- **Card Shadows**: `shadow` or `shadow-lg`
- **Card Padding**: `p-6` for content areas

#### Status and Feedback
- **Success**: `bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200`
- **Error**: `bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200`
- **Warning**: `bg-yellow-50 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-200`
- **Info**: `bg-blue-50 dark:bg-blue-900/20 text-blue-800 dark:text-blue-200`

## Recent Updates

### Auth Pages Styling (2025-08-30)
- ✅ Standardized all authentication forms with project design system
- ✅ Added comprehensive dark mode support across all auth components
- ✅ Replaced custom gradients with consistent gray backgrounds
- ✅ Updated form inputs, labels, and interactive elements for dark mode
- ✅ Used consistent Turtle icon from main app in AuthPage header

### Layout Standardization (2025-08-30)
- ✅ Updated BrokersPage to match algo-platform layout pattern
- ✅ Standardized Dashboard heading size (text-2xl)
- ✅ Updated placeholder routes with consistent layout containers
- ✅ Removed arbitrary width constraints (`max-w-7xl mx-auto`)

## Component Architecture

### Authentication Components
- **AuthPage**: Main auth container with consistent styling
- **LoginForm**: Email/phone login with dark mode support
- **RegisterForm**: User registration with Indian market validation
- **ForgotPasswordForm**: Password reset flow
- **ResetPasswordForm**: Password reset confirmation
- **EmailVerificationForm**: Email verification process

### Layout Components
- **Layout**: Main layout with sidebar and responsive padding
- **Header**: Top navigation with user menu
- **Sidebar**: Navigation menu with proper mobile support

### Page Components
- **Dashboard**: Welcome page with profile summary and stats
- **BrokersPage**: Broker account management interface

## Development Commands

### Development Server
```bash
cd frontend
npm start
```

### Build and Deploy
```bash
npm run build
```

### Testing
```bash
npm test
```

## Common Patterns

### Error Handling
Always use consistent error message styling:
```tsx
{error && (
  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
    <div className="flex items-center gap-2">
      <XCircle className="h-5 w-5 text-red-600" />
      <span className="text-red-800 dark:text-red-200">{error}</span>
    </div>
  </div>
)}
```

### Loading States
Use consistent loading indicators:
```tsx
{loading && (
  <div className="flex items-center justify-center py-12">
    <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
    <span className="ml-2 text-gray-600 dark:text-gray-400">Loading...</span>
  </div>
)}
```

### Table Styling
Use consistent table styling across all data tables:
```tsx
<table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
  <thead className="bg-gray-50 dark:bg-gray-700">
    <tr>
      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
        Header
      </th>
    </tr>
  </thead>
  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
    <tr className="hover:bg-gray-50 dark:hover:bg-gray-700">
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
        Content
      </td>
    </tr>
  </tbody>
</table>
```

## Integration Notes

### API Integration
- All API calls use axios with interceptors for auth headers
- Consistent error handling across all services
- Environment-based API URL configuration

### State Management
- AuthContext for user authentication state
- Component-level state for page-specific data
- Consistent loading and error state patterns

## Future Development Guidelines

When creating new pages or components:
1. **ALWAYS** start with the standard layout pattern
2. Use the established design system components
3. Implement full dark mode support from the beginning
4. Follow existing API service patterns
5. Include proper error handling and loading states
6. Test on both desktop and mobile viewports