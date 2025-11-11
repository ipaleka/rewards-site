


# Class: ClaimComponent

Defined in: [src/ClaimComponent.ts:17](https://github.com/ipaleka/rewards-site/blob/main/rewardsweb/frontend/src/ClaimComponent.ts#L17)

Component for handling reward claim operations.

Manages the UI and logic for checking claimable status and submitting
claim transactions to the blockchain. Automatically updates when wallet
state changes.

## Example

```typescript
const claimComponent = new ClaimComponent(rewardsClient, walletManager)
claimComponent.bind(document.getElementById('claim-container'))
```

## Constructors

### Constructor

> **new ClaimComponent**(`rewardsClient`, `walletManager`): `ClaimComponent`

Defined in: [src/ClaimComponent.ts:29](https://github.com/ipaleka/rewards-site/blob/main/rewardsweb/frontend/src/ClaimComponent.ts#L29)

Creates an instance of ClaimComponent.

#### Parameters

##### rewardsClient

[`RewardsClient`](../../RewardsClient/classes/RewardsClient.md)

The client for interacting with rewards contract

##### walletManager

`WalletManager`

The wallet manager for account state management

#### Returns

`ClaimComponent`

## Properties

### claimable

> `private` **claimable**: `boolean` = `false`

Defined in: [src/ClaimComponent.ts:21](https://github.com/ipaleka/rewards-site/blob/main/rewardsweb/frontend/src/ClaimComponent.ts#L21)

***

### element

> `private` **element**: `HTMLElement` \| `null` = `null`

Defined in: [src/ClaimComponent.ts:18](https://github.com/ipaleka/rewards-site/blob/main/rewardsweb/frontend/src/ClaimComponent.ts#L18)

***

### rewardsClient

> `private` **rewardsClient**: [`RewardsClient`](../../RewardsClient/classes/RewardsClient.md)

Defined in: [src/ClaimComponent.ts:19](https://github.com/ipaleka/rewards-site/blob/main/rewardsweb/frontend/src/ClaimComponent.ts#L19)

***

### walletManager

> `private` **walletManager**: `WalletManager`

Defined in: [src/ClaimComponent.ts:20](https://github.com/ipaleka/rewards-site/blob/main/rewardsweb/frontend/src/ClaimComponent.ts#L20)

## Methods

### addEventListeners()

> `private` **addEventListeners**(): `void`

Defined in: [src/ClaimComponent.ts:126](https://github.com/ipaleka/rewards-site/blob/main/rewardsweb/frontend/src/ClaimComponent.ts#L126)

Adds event listeners for user interactions.

Listens for click events on the claim button.

#### Returns

`void`

***

### bind()

> **bind**(`element`): `void`

Defined in: [src/ClaimComponent.ts:40](https://github.com/ipaleka/rewards-site/blob/main/rewardsweb/frontend/src/ClaimComponent.ts#L40)

Binds the component to a DOM element and initializes event listeners.

#### Parameters

##### element

`HTMLElement`

The HTML element to bind the component to

#### Returns

`void`

***

### checkClaimableStatus()

> `private` **checkClaimableStatus**(): `Promise`\<`void`\>

Defined in: [src/ClaimComponent.ts:54](https://github.com/ipaleka/rewards-site/blob/main/rewardsweb/frontend/src/ClaimComponent.ts#L54)

Checks if the current account has any claimable rewards.

Fetches claimable status from the backend API and updates the UI accordingly.
Handles errors by setting claimable to false and re-rendering.

#### Returns

`Promise`\<`void`\>

***

### destroy()

> **destroy**(): `void`

Defined in: [src/ClaimComponent.ts:142](https://github.com/ipaleka/rewards-site/blob/main/rewardsweb/frontend/src/ClaimComponent.ts#L142)

Cleans up the component.

Currently no specific cleanup needed, but provided for interface consistency.

#### Returns

`void`

***

### handleClaim()

> `private` **handleClaim**(): `Promise`\<`void`\>

Defined in: [src/ClaimComponent.ts:81](https://github.com/ipaleka/rewards-site/blob/main/rewardsweb/frontend/src/ClaimComponent.ts#L81)

Handles the claim transaction submission.

Submits a claim transaction to the blockchain and updates the UI
based on the result. Re-checks claimable status after completion.

#### Returns

`Promise`\<`void`\>

***

### render()

> `private` **render**(): `void`

Defined in: [src/ClaimComponent.ts:109](https://github.com/ipaleka/rewards-site/blob/main/rewardsweb/frontend/src/ClaimComponent.ts#L109)

Renders the current claimable status to the UI.

Updates the claim button state and text based on whether rewards
are currently claimable.

#### Returns

`void`
