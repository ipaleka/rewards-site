# Frontend package

TypeScript/JavaScript frontend application built with Vite.

> **Note**: The frontend documentation is generated using TypeDoc. For detailed API documentation, see the generated TypeDoc output.

## Overview

The frontend is a TypeScript application that provides the user interface for interacting with the Algorand blockchain and managing rewards. It uses the `@txnlab/use-wallet` library for wallet management and integrates with a Django backend for authentication and data management.

## Architecture

The frontend follows a component-based architecture where each major functionality is encapsulated in its own class. The main application orchestrates these components and manages their lifecycle.

## Main components

### App (main.ts)

Main application orchestrator that initializes and coordinates all components.

**Location**: `rewardsweb/frontend/src/main.ts`

**Responsibilities**:

* Initialize application on DOM content loaded
* Fetch initial wallet and network data
* Create and bind all UI components
* Manage application lifecycle and cleanup
* Handle wallet session resumption

**Key features**:

* Component lifecycle management
* Error handling for initialization
* Proper cleanup on page unload
* Coordination between components

### ActiveNetwork

Manages network selection and synchronization between the UI and backend.

**Location**: `rewardsweb/frontend/src/ActiveNetwork.ts`

**Responsibilities**:

* Display current active network in the UI
* Handle network selection via button clicks
* Synchronize network changes with backend API
* Manage CSRF token for secure API calls

**Key methods**:

* `bind(element)` - Binds the component to a DOM element
* `destroy()` - Cleans up event listeners and subscriptions

### WalletComponent

Handles individual wallet connections, authentication, and transaction signing.

**Location**: `rewardsweb/frontend/src/WalletComponent.ts`

**Responsibilities**:

* Manage wallet connection/disconnection
* Handle user authentication with cryptographic signing
* Send test transactions
* Manage active account selection
* Render wallet state to UI

**Key methods**:

* `connect()` - Connects the wallet
* `disconnect()` - Disconnects the wallet
* `auth()` - Authenticates user with backend
* `sendTransaction()` - Sends test transaction

### ClaimComponent

Manages reward claim operations and status checking.

**Location**: `rewardsweb/frontend/src/ClaimComponent.ts`

**Responsibilities**:

* Check claimable status for current account
* Submit claim transactions to blockchain
* Update UI based on claimable status
* Handle claim transaction errors

**Key methods**:

* `checkClaimableStatus()` - Fetches claimable status from backend
* `handleClaim()` - Submits claim transaction

### AddAllocationsComponent

Manages adding reward allocations to multiple addresses.

**Location**: `rewardsweb/frontend/src/AddAllocationsComponent.ts`

**Responsibilities**:

* Fetch allocation data from backend API
* Render addresses and amounts in UI
* Submit add allocations transactions
* Handle user input from textareas

**Key methods**:

* `fetchAllocationsData()` - Fetches allocation data
* `handleAddAllocations()` - Submits allocation transaction

### ReclaimAllocationsComponent

Handles reclaiming allocated rewards from ineligible addresses.

**Location**: `rewardsweb/frontend/src/ReclaimAllocationsComponent.ts`

**Responsibilities**:

* Fetch reclaimable addresses from backend
* Render list of reclaimable addresses with action buttons
* Submit individual reclaim transactions
* Handle reclaim errors per address

**Key methods**:

* `fetchReclaimAllocationsData()` - Fetches reclaimable addresses
* `handleReclaimAllocation()` - Reclaims from specific address

## Core services

### RewardsClient

Main client for interacting with Rewards smart contract and backend API.

**Location**: `rewardsweb/frontend/src/RewardsClient.ts`

**Responsibilities**:

* Compose and submit blockchain transactions
* Interact with Rewards smart contract ABI
* Handle atomic transaction groups
* Manage CSRF tokens for API calls
* Fetch data from backend endpoints

**Key methods**:

* `addAllocations()` - Adds allocations to multiple addresses
* `reclaimAllocation()` - Reclaims allocation from address
* `claim()` - Claims rewards for current account
* Various data fetching methods for backend API

**Contract interactions**:

* Uses Atomic Transaction Composer for complex transactions
* Handles asset opt-in for reward tokens
* Manages different app IDs per network (Testnet/Mainnet)

## Development

To work with the frontend:

```bash
cd rewardsweb/frontend
npm install          # Install dependencies
npm run dev          # Start development server
npm run build        # Build for production
npm run test         # Run tests
npm run build:docs   # Generate TypeDoc documentation