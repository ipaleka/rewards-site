[**rewards-frontend-package**](../../README.md)

***

[rewards-frontend-package](../../modules.md) / [AddAllocationsComponent](../README.md) / AddAllocationsComponent

# Class: AddAllocationsComponent

Defined in: [src/AddAllocationsComponent.ts:17](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/AddAllocationsComponent.ts#L17)

Component for managing and adding reward allocations to multiple addresses.

This component handles the UI and logic for adding allocations to various addresses
with corresponding amounts. It integrates with the RewardsClient to fetch data
and submit transactions to the blockchain.

## Example

```typescript
const addAllocationsComponent = new AddAllocationsComponent(rewardsClient, walletManager)
addAllocationsComponent.bind(document.getElementById('add-allocations-container'))
```

## Constructors

### Constructor

> **new AddAllocationsComponent**(`rewardsClient`, `walletManager`): `AddAllocationsComponent`

Defined in: [src/AddAllocationsComponent.ts:30](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/AddAllocationsComponent.ts#L30)

Creates an instance of AddAllocationsComponent.

#### Parameters

##### rewardsClient

[`RewardsClient`](../../RewardsClient/classes/RewardsClient.md)

The client for interacting with rewards contract and API

##### walletManager

`WalletManager`

The wallet manager for account and network state

#### Returns

`AddAllocationsComponent`

## Properties

### addresses

> `private` **addresses**: `string`[] = `[]`

Defined in: [src/AddAllocationsComponent.ts:21](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/AddAllocationsComponent.ts#L21)

***

### amounts

> `private` **amounts**: `number`[] = `[]`

Defined in: [src/AddAllocationsComponent.ts:22](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/AddAllocationsComponent.ts#L22)

***

### element

> `private` **element**: `HTMLElement` \| `null` = `null`

Defined in: [src/AddAllocationsComponent.ts:18](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/AddAllocationsComponent.ts#L18)

***

### rewardsClient

> `private` **rewardsClient**: [`RewardsClient`](../../RewardsClient/classes/RewardsClient.md)

Defined in: [src/AddAllocationsComponent.ts:19](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/AddAllocationsComponent.ts#L19)

***

### walletManager

> `private` **walletManager**: `WalletManager`

Defined in: [src/AddAllocationsComponent.ts:20](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/AddAllocationsComponent.ts#L20)

## Methods

### addEventListeners()

> `private` **addEventListeners**(): `void`

Defined in: [src/AddAllocationsComponent.ts:121](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/AddAllocationsComponent.ts#L121)

Adds event listeners for user interactions.

Listens for click events on the add allocations button and updates
internal state from textarea inputs before submission.

#### Returns

`void`

***

### bind()

> **bind**(`element`): `void`

Defined in: [src/AddAllocationsComponent.ts:41](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/AddAllocationsComponent.ts#L41)

Binds the component to a DOM element and initializes event listeners.

#### Parameters

##### element

`HTMLElement`

The HTML element to bind the component to

#### Returns

`void`

***

### destroy()

> **destroy**(): `void`

Defined in: [src/AddAllocationsComponent.ts:137](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/AddAllocationsComponent.ts#L137)

Cleans up the component.

Currently no specific cleanup needed, but provided for interface consistency.

#### Returns

`void`

***

### fetchAllocationsData()

> `private` **fetchAllocationsData**(): `Promise`\<`void`\>

Defined in: [src/AddAllocationsComponent.ts:55](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/AddAllocationsComponent.ts#L55)

Fetches allocation data from the backend API for the active account.

Updates the internal state with addresses and amounts, then re-renders the UI.
Handles errors by displaying alerts to the user.

#### Returns

`Promise`\<`void`\>

***

### handleAddAllocations()

> `private` **handleAddAllocations**(): `Promise`\<`void`\>

Defined in: [src/AddAllocationsComponent.ts:88](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/AddAllocationsComponent.ts#L88)

Handles the add allocations transaction submission.

Sends the current addresses and amounts to the blockchain via RewardsClient.
Displays success/error messages and refreshes data on success.

#### Returns

`Promise`\<`void`\>

***

### render()

> `private` **render**(): `void`

Defined in: [src/AddAllocationsComponent.ts:108](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/AddAllocationsComponent.ts#L108)

Renders the current allocation data to the UI.

Updates textareas and display elements with current addresses and amounts.

#### Returns

`void`
