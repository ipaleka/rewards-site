[**rewards-frontend-package**](../../README.md)

***

[rewards-frontend-package](../../modules.md) / [RewardsClient](../README.md) / RewardsClient

# Class: RewardsClient

Defined in: [src/RewardsClient.ts:24](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/RewardsClient.ts#L24)

Client for interacting with the Rewards smart contract and backend API.

This class provides methods to interact with the Algorand blockchain
for reward-related operations including adding allocations, reclaiming
allocations, and claiming rewards. It handles transaction composition,
signing, and submission.

## Example

```typescript
const rewardsClient = new RewardsClient(wallet, walletManager)
await rewardsClient.addAllocations(addresses, amounts)
```

## Constructors

### Constructor

> **new RewardsClient**(`wallet`, `manager`): `RewardsClient`

Defined in: [src/RewardsClient.ts:37](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/RewardsClient.ts#L37)

Creates an instance of RewardsClient.

#### Parameters

##### wallet

`BaseWallet`

The wallet instance for transaction signing

##### manager

`WalletManager`

The wallet manager for network and account management

#### Returns

`RewardsClient`

## Properties

### algodClient

> `private` **algodClient**: `AlgodClient`

Defined in: [src/RewardsClient.ts:27](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/RewardsClient.ts#L27)

***

### contract

> `private` **contract**: `ABIContract`

Defined in: [src/RewardsClient.ts:28](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/RewardsClient.ts#L28)

***

### manager

> `private` **manager**: `WalletManager`

Defined in: [src/RewardsClient.ts:26](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/RewardsClient.ts#L26)

***

### rewardsAppIds

> `private` **rewardsAppIds**: `object`

Defined in: [src/RewardsClient.ts:29](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/RewardsClient.ts#L29)

#### betanet?

> `optional` **betanet**: `number`

#### fnet?

> `optional` **fnet**: `number`

#### localnet?

> `optional` **localnet**: `number`

#### mainnet?

> `optional` **mainnet**: `number`

#### testnet?

> `optional` **testnet**: `number`

***

### wallet

> `private` **wallet**: `BaseWallet`

Defined in: [src/RewardsClient.ts:25](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/RewardsClient.ts#L25)

## Methods

### addAllocations()

> **addAllocations**(`addresses`, `amounts`): `Promise`\<\{ \}\>

Defined in: [src/RewardsClient.ts:83](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/RewardsClient.ts#L83)

Adds allocations to multiple addresses with specified amounts.

Creates and submits an atomic transaction to the rewards contract
to allocate rewards to the provided addresses.

#### Parameters

##### addresses

`string`[]

Array of recipient addresses

##### amounts

`number`[]

Array of amounts to allocate (must match addresses length)

#### Returns

`Promise`\<\{ \}\>

The transaction result

#### Throws

When no active account, arrays are empty, or arrays length mismatch

***

### claim()

> **claim**(): `Promise`\<\{ \}\>

Defined in: [src/RewardsClient.ts:178](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/RewardsClient.ts#L178)

Claims available rewards for the active account.

Performs an atomic transaction group that includes:
1. Asset opt-in transaction for the reward token
2. Claim method call to the rewards contract

#### Returns

`Promise`\<\{ \}\>

The transaction result

#### Throws

When no active account, app ID not configured, or token_id not found

***

### fetchAddAllocationsData()

> **fetchAddAllocationsData**(`address`): `Promise`\<\{ `addresses`: `string`[]; `amounts`: `number`[]; \}\>

Defined in: [src/RewardsClient.ts:296](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/RewardsClient.ts#L296)

Fetches add allocations data for an address from the backend API.

#### Parameters

##### address

`string`

The address to fetch allocation data for

#### Returns

`Promise`\<\{ `addresses`: `string`[]; `amounts`: `number`[]; \}\>

Object containing addresses and amounts for allocations

#### Throws

When the API request fails

***

### fetchClaimableStatus()

> **fetchClaimableStatus**(`address`): `Promise`\<\{ `claimable`: `boolean`; \}\>

Defined in: [src/RewardsClient.ts:253](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/RewardsClient.ts#L253)

Fetches the claimable status for an address from the backend API.

#### Parameters

##### address

`string`

The address to check claimable status for

#### Returns

`Promise`\<\{ `claimable`: `boolean`; \}\>

Object indicating whether rewards are claimable

#### Throws

When the API request fails

***

### fetchReclaimAllocationsData()

> **fetchReclaimAllocationsData**(`address`): `Promise`\<\{ `addresses`: `string`[]; \}\>

Defined in: [src/RewardsClient.ts:321](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/RewardsClient.ts#L321)

Fetches reclaimable allocations data for an address from the backend API.

#### Parameters

##### address

`string`

The address to fetch reclaimable data for

#### Returns

`Promise`\<\{ `addresses`: `string`[]; \}\>

Object containing addresses with reclaimable allocations

#### Throws

When the API request fails

***

### getCsrfToken()

> `private` **getCsrfToken**(): `string`

Defined in: [src/RewardsClient.ts:56](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/RewardsClient.ts#L56)

Retrieves the CSRF token from cookies or form input for API requests.

#### Returns

`string`

The CSRF token as a string

***

### getHeaders()

> `private` **getHeaders**(): `object`

Defined in: [src/RewardsClient.ts:67](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/RewardsClient.ts#L67)

Gets the headers for API requests including CSRF token.

#### Returns

`object`

Headers object for fetch requests

##### Content-Type

> **Content-Type**: `string` = `'application/json'`

##### X-CSRFToken

> **X-CSRFToken**: `string`

***

### reclaimAllocation()

> **reclaimAllocation**(`userAddress`): `Promise`\<\{ \}\>

Defined in: [src/RewardsClient.ts:132](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/RewardsClient.ts#L132)

Reclaims an allocation from a specific user address.

Submits a transaction to reclaim previously allocated rewards from
the specified address back to the contract owner.

#### Parameters

##### userAddress

`string`

The address to reclaim allocation from

#### Returns

`Promise`\<\{ \}\>

The transaction result

#### Throws

When no active account or app ID not configured

***

### userClaimed()

> **userClaimed**(`address`): `Promise`\<\{ `success`: `boolean`; \}\>

Defined in: [src/RewardsClient.ts:271](https://github.com/ipaleka/rewards-site/blob/c26018d7a38f4b103bc927d56c383b2a4627b7bc/rewardsweb/frontend/src/RewardsClient.ts#L271)

#### Parameters

##### address

`string`

#### Returns

`Promise`\<\{ `success`: `boolean`; \}\>
