# Frontend Requirements & Design Specification

## Overview

This document outlines the frontend requirements for the Azure AI Chatbot application with MCP OAuth Identity Passthrough support. The application must provide a seamless, mobile-responsive experience for enterprise users.

---

## Core Requirements

### 1. Authentication (Azure Entra ID)

| Requirement | Priority | Status |
|-------------|----------|--------|
| Popup-based OAuth 2.0 login | Must Have | ✅ Exists |
| Automatic token refresh | Must Have | ✅ Exists |
| User profile display (name, email, avatar) | Must Have | ✅ Exists |
| Sign out functionality | Must Have | ✅ Exists |
| Session persistence | Should Have | ✅ Exists |
| Multi-tab session sync | Nice to Have | ❌ New |

**Flow:**
```
User clicks "Sign In" 
    → Azure AD popup opens 
    → User authenticates 
    → Token received via MSAL 
    → Redirect to Agent Selection
```

---

### 2. Agent Selection & Switching

| Requirement | Priority | Status |
|-------------|----------|--------|
| Grid/List view of available agents | Must Have | ✅ Exists |
| Agent card with name, description, model | Must Have | ✅ Exists |
| Agent capabilities display | Should Have | ✅ Exists |
| **RBAC-filtered agent list** | Must Have | ❌ New |
| **MCP connection status per agent** | Must Have | ❌ New |
| Quick agent switch from chat | Should Have | ❌ New |
| Agent search/filter | Nice to Have | ❌ New |
| Favorite agents | Nice to Have | ❌ New |

**New: MCP Status Indicator**
```
┌─────────────────────────────────────┐
│  🤖 GitHub Assistant                │
│  Access your repos, commits, PRs    │
│                                     │
│  Model: gpt-4o                      │
│  ┌───────────────────────────────┐  │
│  │ 🔗 GitHub   ✅ Connected      │  │
│  │ 📧 Outlook  ⚠️ Not Connected  │  │
│  └───────────────────────────────┘  │
│                     [Select Agent]  │
└─────────────────────────────────────┘
```

---

### 3. Chat Interface

| Requirement | Priority | Status |
|-------------|----------|--------|
| Message input with send button | Must Have | ✅ Exists |
| User/Assistant message bubbles | Must Have | ✅ Exists |
| Typing indicator | Must Have | ✅ Exists |
| Markdown rendering in responses | Must Have | ✅ Exists |
| Code syntax highlighting | Should Have | ❌ New |
| Message timestamps | Should Have | ❌ New |
| Copy message button | Should Have | ❌ New |
| Streaming responses | Must Have | ✅ Exists |
| Enter to send / Shift+Enter for newline | Must Have | ✅ Exists |
| **MCP tool call indicators** | Must Have | ❌ New |
| **MCP consent modal integration** | Must Have | ❌ New |

**New: MCP Tool Call Display**
```
┌─────────────────────────────────────┐
│ 🔧 Calling GitHub MCP...            │
│ └─ Tool: get_commits                │
│ └─ Repo: user/my-project            │
└─────────────────────────────────────┘
```

---

### 4. Chat History & Session Management

| Requirement | Priority | Status |
|-------------|----------|--------|
| Session list in sidebar | Must Have | ❌ Enhanced |
| Session title (auto-generated) | Must Have | ✅ Exists |
| Load previous sessions | Must Have | ✅ Exists |
| **New Chat button** | Must Have | ❌ New |
| Delete session | Should Have | ❌ New |
| Rename session | Nice to Have | ❌ New |
| Search chat history | Nice to Have | ❌ New |
| Session grouped by date | Nice to Have | ❌ New |

**Layout:**
```
┌──────────────────────────────────────────────────────┐
│ ☰  Azure AI Chatbot            👤 User Name  [↪]    │
├─────────────┬────────────────────────────────────────┤
│ [+ New Chat]│  🤖 GitHub Assistant                   │
│             │                                        │
│ Today       │  User: Show my recent commits          │
│ ├─ Chat 1   │                                        │
│ └─ Chat 2   │  🔧 Calling github.get_commits...      │
│             │                                        │
│ Yesterday   │  Assistant: Here are your commits:     │
│ └─ Chat 3   │  • fix: resolve login bug (2h ago)     │
│             │  • feat: add MCP support (5h ago)      │
│             │                                        │
│             │  ────────────────────────────────────  │
│             │  │ Type your message...        [➤] │  │
│             │  ────────────────────────────────────  │
└─────────────┴────────────────────────────────────────┘
```

---

### 5. MCP OAuth Identity Passthrough (NEW)

| Requirement | Priority | Status |
|-------------|----------|--------|
| **MCP consent modal** | Must Have | ❌ New |
| **Connected services indicator** | Must Have | ❌ New |
| **Disconnect service option** | Should Have | ❌ New |
| **Re-authentication prompt** | Must Have | ❌ New |
| **MCP settings page** | Should Have | ❌ New |

**Consent Flow UI:**
```
┌─────────────────────────────────────────┐
│     🔗 Connect to GitHub                │
│                                         │
│  This agent needs access to your        │
│  GitHub account to help you.            │
│                                         │
│  Permissions requested:                 │
│  • Read your repositories               │
│  • View commits and pull requests       │
│                                         │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │   Cancel    │  │ Connect GitHub  │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
```

**Connected Services Display (in Settings or Sidebar):**
```
┌─────────────────────────────────────────┐
│  Your Connected Services                │
│                                         │
│  ✅ GitHub         [Disconnect]         │
│     Connected as: user@example.com      │
│                                         │
│  ⚠️ Outlook        [Connect Now]        │
│     Not connected                       │
│                                         │
│  ⚠️ SharePoint     [Connect Now]        │
│     Not connected                       │
└─────────────────────────────────────────┘
```

---

### 6. Mobile Responsive Design

| Breakpoint | Layout Changes |
|------------|----------------|
| **Desktop (≥1024px)** | Sidebar visible, full chat area |
| **Tablet (768-1023px)** | Collapsible sidebar, touch-friendly |
| **Mobile (≤767px)** | Bottom nav, swipe gestures, full-screen chat |

**Mobile Layout:**
```
┌─────────────────────────┐
│ ☰  GitHub Assistant  👤 │  ← Header with hamburger menu
├─────────────────────────┤
│                         │
│  User: Show commits     │
│                         │
│  🤖 Here are your       │
│  recent commits:        │
│  • fix: login bug       │
│                         │
│                         │
├─────────────────────────┤
│ Type message...    [➤]  │  ← Fixed input area
├─────────────────────────┤
│ 💬  🤖  ⚙️              │  ← Bottom navigation
└─────────────────────────┘
   Chat Agents Settings
```

**Mobile Considerations:**
- Touch-friendly buttons (min 44x44px)
- Swipe to open/close sidebar
- Pull-to-refresh for messages
- Keyboard-aware input positioning
- Safe area insets (for notched devices)

---

### 7. Error Handling & Loading States

| State | UI Treatment |
|-------|--------------|
| Initial loading | Skeleton screens |
| Sending message | Disabled input + spinner |
| Agent thinking | Typing indicator dots |
| MCP tool executing | Tool call card with spinner |
| OAuth consent needed | Modal with connect button |
| Network error | Toast notification + retry button |
| Session expired | Redirect to login with message |
| Rate limited | Toast with wait time |

---

### 8. Accessibility (WCAG 2.1 AA)

| Requirement | Implementation |
|-------------|----------------|
| Keyboard navigation | Tab order, focus visible |
| Screen reader support | ARIA labels, live regions |
| Color contrast | 4.5:1 minimum |
| Reduced motion | Respect prefers-reduced-motion |
| Focus management | Trap focus in modals |
| Skip links | Skip to main content |

---

## Component Hierarchy

```
App
├── AuthProvider (MSAL context)
│   └── AppContent
│       ├── Login (unauthenticated)
│       └── MainLayout (authenticated)
│           ├── Sidebar
│           │   ├── UserProfile
│           │   ├── NewChatButton
│           │   ├── SessionList
│           │   └── MCPConnectionStatus (NEW)
│           ├── MainArea
│           │   ├── AgentSelection (no agent selected)
│           │   │   ├── AgentCard
│           │   │   └── MCPBadges (NEW)
│           │   └── Chat (agent selected)
│           │       ├── ChatHeader
│           │       ├── MessageList
│           │       │   ├── UserMessage
│           │       │   ├── AssistantMessage
│           │       │   └── MCPToolCallCard (NEW)
│           │       └── ChatInput
│           └── MCPConsentModal (NEW)
```

---

## New Components Required

### 1. MCPConsentModal
- Displayed when agent requires OAuth consent
- Shows service name, permissions, connect/cancel buttons
- Opens OAuth popup on connect

### 2. MCPConnectionStatus
- Shows all MCP servers and their connection state
- Allows connect/disconnect actions

### 3. MCPToolCallCard
- Displays during agent tool execution
- Shows tool name, arguments (sanitized), status

### 4. SessionSidebar
- Enhanced sidebar with session management
- New chat, session list, grouped by date

### 5. AgentSwitcher
- Quick agent switch from chat header
- Shows current agent with dropdown

---

## State Management

```typescript
interface AppState {
  // Auth
  isAuthenticated: boolean;
  user: UserProfile | null;
  accessToken: string | null;

  // Agents
  agents: Agent[];
  selectedAgent: Agent | null;
  agentLoading: boolean;

  // Sessions
  sessions: ChatSession[];
  activeSession: ChatSession | null;
  messages: ChatMessage[];

  // MCP (NEW)
  mcpServers: MCPServer[];
  mcpConnections: Record<string, MCPConnection>;
  pendingConsent: MCPConsentRequest | null;

  // UI
  sidebarOpen: boolean;
  isMobile: boolean;
}
```

---

## API Integration Points

| Endpoint | Component | Purpose |
|----------|-----------|---------|
| `GET /api/auth/me` | AuthProvider | Get user profile |
| `GET /api/agents` | AgentSelection | List agents (RBAC filtered) |
| `GET /api/sessions` | SessionSidebar | List user sessions |
| `POST /api/sessions` | NewChatButton | Create new session |
| `DELETE /api/sessions/{id}` | SessionList | Delete session |
| `POST /api/chat` | ChatInput | Send message |
| `GET /api/mcp/servers` | MCPConnectionStatus | List MCP servers |
| `POST /api/mcp/consent-callback` | MCPConsentModal | Store consent result |

---

## Design Tokens

```css
:root {
  /* Colors */
  --color-primary: #0066FF;
  --color-primary-hover: #0052CC;
  --color-success: #22C55E;
  --color-warning: #F59E0B;
  --color-error: #EF4444;
  --color-surface: #FFFFFF;
  --color-surface-secondary: #F8FAFC;
  --color-text: #1E293B;
  --color-text-muted: #64748B;

  /* Spacing */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;

  /* Borders */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
}
```

---

## Client Expectations Checklist

| Requirement | Customer Need | Implementation |
|-------------|---------------|----------------|
| ✅ Entra ID Login | Enterprise SSO | MSAL popup flow |
| ✅ Mobile Responsive | Field workers, executives | Tailwind responsive classes |
| ✅ Agent Switching | Multiple use cases | Agent selection grid |
| ✅ Chat History | Context continuity | Session persistence |
| ✅ New Chat | Fresh conversations | New chat button + API |
| ⭐ MCP OAuth | Access user's GitHub/Outlook/SharePoint | Consent modal + token storage |
| ⭐ RBAC Visibility | Secure agent access | Filtered agent list |
| ⏳ RAG Integration | Knowledge base access | Backend integration |

**Legend:** ✅ Exists | ⭐ Must Build | ⏳ Future Phase

---

## Implementation Priority

### Phase 1A: MCP OAuth UI (3 days)
1. MCPConsentModal component
2. MCPConnectionStatus component
3. Handle 428 response in Chat
4. MCPToolCallCard for tool visibility

### Phase 1B: Session Management (2 days)
1. Enhanced SessionSidebar
2. New Chat button + flow
3. Session delete functionality

### Phase 1C: Mobile Optimization (1 day)
1. Mobile navigation
2. Gesture support
3. Touch-friendly interactions

---

*Created: December 17, 2025*
