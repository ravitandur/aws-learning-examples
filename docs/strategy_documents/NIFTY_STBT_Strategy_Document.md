# NIFTY STBT (Short Straddle Buy Tomorrow) Strategy Document

**Version:** 1.0
**Date:** October 11, 2025
**Status:** Pending Partner Approval
**Classification:** For Mock Testing & Evaluation

---

## Executive Summary

**NIFTY_STBT** is a positional short straddle strategy designed for overnight premium collection on NIFTY 50 index options. The strategy enters short positions (sell both Call and Put options with ~₹100 premium each) at 9:19 AM and exits the next trading day at 9:18 AM. With a capital allocation of ₹4,00,000, the strategy targets consistent small profits through time decay while employing sophisticated risk controls including 20-point stop losses, re-entry logic (up to 2 additional entries), and wait-and-trade mechanisms (6% threshold). Designed for non-expiry days only to avoid heightened expiry volatility, this strategy is suitable for experienced traders comfortable with overnight positional risk and unlimited downside potential inherent in short options strategies.

**Key Metrics:**
- **Target Win Rate:** 30%
- **Risk-Reward Ratio:** 1:6
- **Expected Monthly Profit:** ₹2,000 (0.5% on capital)
- **Maximum Drawdown:** ₹6,000 (1.5% of capital)
- **Capital Required:** ₹4,00,000 (₹2,00,000 per set)

---

## Strategy Configuration

### Core Parameters

| Parameter | Value |
|-----------|-------|
| **Strategy Name** | NIFTY_STBT (Short Straddle Buy Tomorrow) |
| **Strategy ID** | S1 |
| **Basket Name** | STBT100 |
| **Capital Allocation** | ₹4,00,000 per basket |
| **Product Type** | Positional (NRML) |
| **Intraday Strategy** | No (Overnight holding) |
| **Execution Days** | Monday to Friday (Non-Expiry only) |
| **Index** | NIFTY 50 |
| **Strategy Type** | ExitNextDay (Time-based exit) |

### Position Structure

```
Strategy: Short Straddle
├─ Leg 1: Sell NIFTY Call (CE) @ ~₹100 premium
└─ Leg 2: Sell NIFTY Put (PE) @ ~₹100 premium

Holding Period: Overnight (Entry 9:19 AM → Exit Next Day 9:18 AM)
```

---

## Entry & Exit Logic

### Entry Rules

**Entry Time:** 9:19:00 AM IST
**Entry Day:** Monday to Friday (excluding NIFTY expiry days)

#### Strike Selection Logic:
- **Method:** CLOSEST_PREMIUM algorithm
- **Target Premium:** ₹100 per leg
- **Selection Process:**
  1. Fetch all NIFTY option strikes at 9:19 AM
  2. Calculate premium for each Call (CE) and Put (PE) option
  3. Select CE strike with premium closest to ₹100
  4. Select PE strike with premium closest to ₹100
  5. Execute sell orders for both strikes simultaneously

**Example Entry:**
```
NIFTY Spot: 19,500
Selected CE Strike: 19,550 CE @ ₹98 (closest to ₹100)
Selected PE Strike: 19,450 PE @ ₹102 (closest to ₹100)

Orders:
→ Sell NIFTY 19,550 CE @ ₹98 × 25 lots = ₹2,450 credit
→ Sell NIFTY 19,450 PE @ ₹102 × 25 lots = ₹2,550 credit
Total Credit Received: ₹5,000
```

### Exit Rules

**Exit Time:** 9:18:00 AM IST (Next Trading Day)
**Exit Type:** Time-based (ExitNextDay)
**Exit Method:** Buy back both CE and PE positions

#### Exit Schedule by Entry Day:

| Entry Day | Entry Time | Exit Day | Exit Time | Holding Period |
|-----------|------------|----------|-----------|----------------|
| Monday | 09:19 AM | Tuesday | 09:18 AM | ~24 hours |
| Tuesday | 09:19 AM | Wednesday | 09:18 AM | ~24 hours |
| Wednesday | 09:19 AM | Thursday | 09:18 AM | ~24 hours |
| Thursday | 09:19 AM | Friday | 09:18 AM | ~24 hours |
| Friday | 09:19 AM | Monday | 09:18 AM | ~72 hours (weekend) |

**Note:** No execution on NIFTY expiry days (typically last Thursday of the month)

---

## Position Details

### Leg 1: NIFTY Call Option (CE) - Short Position

```yaml
Configuration:
  Leg Number: 1
  Direction: Sell (Short)
  Option Type: Call (CE)
  Base Lots: 1 lot (25 units per NIFTY lot)
  Index: NIFTY 50

Strike Selection:
  Method: CLOSEST_PREMIUM
  Target Premium: ₹100
  Selection Algorithm: Fetch all CE strikes, select strike with premium nearest to ₹100

Entry Execution:
  Order Type: Market Order (MIS/NRML depending on product config)
  Quantity: Lots × 25 units
  Transaction: Sell to Open

Risk Parameters:
  Stop Loss: 20 points from entry premium
  Re-Entry: Up to 2 additional entries after stop loss
  Wait & Trade: 6% move threshold
```

**Example Trade Flow:**
```
Entry:
  Strike: NIFTY 19,550 CE
  Entry Premium: ₹98
  Lots: 1 (25 units)
  Credit Received: ₹98 × 25 = ₹2,450

Stop Loss:
  Trigger Level: ₹98 + ₹20 = ₹118
  If premium reaches ₹118 → Exit with ₹500 loss per lot

Target Exit:
  Exit Time: Next day 9:18 AM
  Exit Premium: ₹60 (assumed decay)
  Profit: (₹98 - ₹60) × 25 = ₹950 per lot
```

### Leg 2: NIFTY Put Option (PE) - Short Position

```yaml
Configuration:
  Leg Number: 2
  Direction: Sell (Short)
  Option Type: Put (PE)
  Base Lots: 1 lot (25 units per NIFTY lot)
  Index: NIFTY 50

Strike Selection:
  Method: CLOSEST_PREMIUM
  Target Premium: ₹100
  Selection Algorithm: Fetch all PE strikes, select strike with premium nearest to ₹100

Entry Execution:
  Order Type: Market Order (MIS/NRML depending on product config)
  Quantity: Lots × 25 units
  Transaction: Sell to Open

Risk Parameters:
  Stop Loss: 20 points from entry premium
  Re-Entry: Up to 2 additional entries after stop loss
  Wait & Trade: 6% move threshold
```

**Example Trade Flow:**
```
Entry:
  Strike: NIFTY 19,450 PE
  Entry Premium: ₹102
  Lots: 1 (25 units)
  Credit Received: ₹102 × 25 = ₹2,550

Stop Loss:
  Trigger Level: ₹102 + ₹20 = ₹122
  If premium reaches ₹122 → Exit with ₹500 loss per lot

Target Exit:
  Exit Time: Next day 9:18 AM
  Exit Premium: ₹70 (assumed decay)
  Profit: (₹102 - ₹70) × 25 = ₹800 per lot
```

---

## Risk Management Parameters

### 1. Stop Loss (Points-Based)

**Configuration:**
- **Type:** Points-based stop loss
- **Value:** 20 points per leg
- **Trigger:** Independent for each leg (CE and PE)
- **Execution:** Market order exit when stop loss breached

**Calculation Logic:**
```
Stop Loss Level = Entry Premium + 20 points

Example:
  Entry CE Premium: ₹98
  Stop Loss: ₹98 + ₹20 = ₹118

  If CE premium reaches ₹118:
    → Exit CE leg immediately
    → Loss = (₹118 - ₹98) × 25 = ₹500 per lot
```

**Slippage Considerations:**
- Market orders may execute 1-3 points beyond stop loss
- Budget ₹75-100 extra loss per lot for slippage
- Total risk per leg: ₹500 + ₹100 = ₹600 maximum

### 2. Re-Entry Logic (Re-Cost)

**Configuration:**
- **Enabled:** Yes
- **Maximum Re-Entries:** 2 additional entries
- **Trigger:** After stop loss exit on any leg
- **Purpose:** Average down cost basis if initial stop loss hit

**Re-Entry Flow:**
```
Initial Entry: Sell CE @ ₹98
    ↓
Stop Loss Hit: Exit @ ₹118 (₹500 loss)
    ↓
Re-Entry 1: Sell CE @ current premium (e.g., ₹95)
    ↓
If Stop Loss Hit Again: Exit and trigger Re-Entry 2
    ↓
Re-Entry 2: Sell CE @ current premium (e.g., ₹92)
    ↓
Maximum 2 re-entries total
```

**Risk Implications:**
- Total capital exposure can increase with re-entries
- Each re-entry adds new stop loss risk (₹500 × 3 = ₹1,500 max per leg)
- Must maintain adequate margin for multiple positions

### 3. Wait & Trade Mechanism

**Configuration:**
- **Enabled:** Yes
- **Trigger Type:** Percentage-based on underlying
- **Threshold:** 6% move in NIFTY
- **Logic:** Delay entry if market showing high volatility

**Wait & Trade Flow:**
```
9:19 AM Entry Time Arrives
    ↓
Check NIFTY movement since market open
    ↓
If NIFTY moved >6% (up or down):
    → Wait for retracement or skip trade
    ↓
If NIFTY moved <6%:
    → Proceed with strategy entry
```

**Example Scenarios:**
```
Scenario 1: Normal Market
  NIFTY Open: 19,500
  NIFTY at 9:19 AM: 19,550 (+0.26%)
  Action: Enter trade (below 6% threshold)

Scenario 2: High Volatility
  NIFTY Open: 19,500
  NIFTY at 9:19 AM: 20,700 (+6.15%)
  Action: Skip entry (exceeds 6% threshold)
```

### 4. Cancelled Order Handling

**Configuration:**
- **Save Cancelled Orders:** False
- **Retry Logic:** No automatic retry if order rejected/cancelled
- **Manual Intervention:** Required for cancelled orders

**Rationale:** Avoids chasing market if initial order fails (better to skip than enter at unfavorable prices)

---

## Execution Schedule

### Daily Execution Calendar

The strategy creates **5 independent strategy instances** (one per weekday) for continuous execution throughout the week. Each instance operates independently with its own entry/exit times.

| Strategy Instance | Entry Day | Entry Time | Exit Day | Exit Time | Status |
|-------------------|-----------|------------|----------|-----------|--------|
| S1_MON | Monday | 09:19:00 | Tuesday | 09:18:00 | Active |
| S1_TUE | Tuesday | 09:19:00 | Wednesday | 09:18:00 | Active |
| S1_WED | Wednesday | 09:19:00 | Thursday | 09:18:00 | Active |
| S1_THU | Thursday | 09:19:00 | Friday | 09:18:00 | Active |
| S1_FRI | Friday | 09:19:00 | Monday | 09:18:00 | Active |

### Expiry Day Exclusions

**NIFTY Expiry:** Last Thursday of each month

**Behavior on Expiry Weeks:**
```
If Thursday is expiry day:
  → S1_WED skips execution (would exit on expiry day)
  → S1_THU skips execution (entry on expiry day)
  → All other days execute normally
```

**Example: October 2025 Expiry Calendar**
```
Week of Oct 27-31 (Expiry: Oct 30)
  Mon, Oct 27: Normal execution (S1_MON)
  Tue, Oct 28: Normal execution (S1_TUE)
  Wed, Oct 29: SKIP (would exit on expiry day)
  Thu, Oct 30: SKIP (expiry day entry)
  Fri, Oct 31: Normal execution (S1_FRI)
```

### Weekend Handling

**Friday → Monday Rollover:**
- Entry: Friday 9:19 AM
- Exit: Monday 9:18 AM
- **Holding Period:** ~72 hours (includes weekend)
- **Additional Risk:** Weekend gap risk if global events occur

---

## Expected Performance Metrics

### Projected Returns

Based on conservative backtesting assumptions and risk parameters:

| Metric | Value | Calculation Basis |
|--------|-------|-------------------|
| **Win Rate** | 30% | 3 out of 10 trades profitable |
| **Average Win** | ₹3,000 | Both legs decay favorably |
| **Average Loss** | ₹1,500 | One or both legs hit stop loss |
| **Risk-Reward Ratio** | 1:6 | ₹500 risk for ₹3,000 reward potential |
| **Monthly Profit** | ₹2,000 | Net profit after wins/losses |
| **Monthly Return** | 0.5% | ₹2,000 / ₹4,00,000 |
| **Annualized Return** | ~6% | Compounded monthly returns |
| **Max Drawdown** | ₹6,000 | 1.5% of capital |
| **Sharpe Ratio** | 0.8-1.2 | Moderate risk-adjusted returns |

### Monthly P&L Projection (22 Trading Days)

```
Assumptions:
  - 22 trading days per month
  - ~20 executable days (excluding expiry days)
  - 30% win rate
  - 2 sets deployed (₹4,00,000 capital)

Monthly Breakdown:
  Winning Trades: 6 trades × ₹3,000 = ₹18,000
  Losing Trades: 14 trades × ₹1,500 = ₹21,000
  Net Monthly P&L: ₹18,000 - ₹21,000 = -₹3,000

  (Note: Actual performance may vary with market conditions)
```

**Performance Scenarios:**

| Scenario | Win Rate | Monthly P&L | Monthly % |
|----------|----------|-------------|-----------|
| Best Case | 50% | +₹10,000 | +2.5% |
| Target Case | 30% | +₹2,000 | +0.5% |
| Worst Case | 10% | -₹6,000 | -1.5% |

---

## Capital Requirements

### Margin Calculation (Per Set)

**NIFTY Lot Size:** 25 units (as of Oct 2025)

#### Initial Margin Requirements:
```
Short Call (CE) Leg:
  SPAN Margin: ~₹50,000
  Exposure Margin: ~₹10,000
  Total CE Margin: ~₹60,000

Short Put (PE) Leg:
  SPAN Margin: ~₹50,000
  Exposure Margin: ~₹10,000
  Total PE Margin: ~₹60,000

Straddle Benefit: -₹20,000 (broker-specific margin benefit)

Net Initial Margin: ₹60,000 + ₹60,000 - ₹20,000 = ₹1,00,000
```

#### Re-Entry Buffer:
```
Buffer for 2 Re-Entries: ₹50,000 × 2 = ₹1,00,000
(50% of initial margin per re-entry)
```

#### Total Capital per Set:
```
Initial Margin: ₹1,00,000
Re-Entry Buffer: ₹1,00,000
Drawdown Buffer: ₹50,000
-------------------------
Total per Set: ₹2,50,000
```

### Recommended Capital Structure

**For ₹4,00,000 Total Capital:**
```
Set 1:
  Allocated Capital: ₹2,00,000
  Initial Margin: ₹1,00,000
  Available Buffer: ₹1,00,000

Set 2:
  Allocated Capital: ₹2,00,000
  Initial Margin: ₹1,00,000
  Available Buffer: ₹1,00,000

Total Deployment: ₹4,00,000
Margin Utilization: 50% (conservative)
```

**Margin Variations:**
- Volatility increases: Margin can increase 20-30%
- Market stress: Margin can double during extreme events
- Always maintain 50%+ buffer beyond stated margin requirements

---

## Scenario Analysis

### Scenario 1: Range-Bound Market (Probability: 40%)

**Market Behavior:**
- NIFTY moves ±0.5% overnight
- Minimal directional movement
- Time decay works in strategy's favor

**Trade Outcome:**
```
Entry: Sell CE @ ₹98, Sell PE @ ₹102 (Total Credit: ₹200/share)
Overnight: NIFTY moves from 19,500 → 19,550 (+0.26%)
Exit: Buy CE @ ₹70, Buy PE @ ₹85

Profit Calculation:
  CE Profit: (₹98 - ₹70) × 25 = ₹700
  PE Profit: (₹102 - ₹85) × 25 = ₹425
  Total Profit: ₹1,125 per set

For 2 Sets: ₹1,125 × 2 = ₹2,250
```

### Scenario 2: Moderate Directional Move (Probability: 30%)

**Market Behavior:**
- NIFTY moves ±2% overnight
- One leg profitable, one leg at loss
- Net result close to breakeven or small profit

**Trade Outcome:**
```
Entry: Sell CE @ ₹98, Sell PE @ ₹102 (Total Credit: ₹200/share)
Overnight: NIFTY moves from 19,500 → 19,900 (+2.05%)
Exit: Buy CE @ ₹150 (loss), Buy PE @ ₹30 (profit)

Profit Calculation:
  CE Loss: (₹98 - ₹150) × 25 = -₹1,300
  PE Profit: (₹102 - ₹30) × 25 = ₹1,800
  Total Profit: ₹500 per set

For 2 Sets: ₹500 × 2 = ₹1,000
```

### Scenario 3: Sharp Move with Stop Loss (Probability: 20%)

**Market Behavior:**
- NIFTY moves ±3-4% overnight
- One or both legs hit stop loss
- Re-entry triggers but may also hit stop loss

**Trade Outcome:**
```
Entry: Sell CE @ ₹98, Sell PE @ ₹102 (Total Credit: ₹200/share)
Overnight: NIFTY moves from 19,500 → 20,280 (+4%)
Stop Loss: CE exits @ ₹118 (stop loss hit)
Exit: Buy PE @ ₹15 (profit)

Profit Calculation:
  CE Loss: (₹98 - ₹118) × 25 = -₹500 (stop loss)
  PE Profit: (₹102 - ₹15) × 25 = ₹2,175
  Net Profit: ₹1,675 per set

If Re-Entry Triggered:
  Re-enter CE @ ₹140, exits @ ₹160 (another ₹500 loss)
  Net Profit: ₹1,675 - ₹500 = ₹1,175 per set
```

### Scenario 4: Black Swan Event (Probability: 10%)

**Market Behavior:**
- NIFTY gaps up/down >5% overnight
- Both legs may hit stop loss or show extreme losses
- Maximum drawdown scenario

**Trade Outcome:**
```
Entry: Sell CE @ ₹98, Sell PE @ ₹102 (Total Credit: ₹200/share)
Overnight: Global crisis, NIFTY gaps down 7% at open
Exit: Both legs at heavy loss

Worst Case:
  CE exits @ ₹10 (profit): (₹98 - ₹10) × 25 = ₹2,200
  PE exits @ ₹250 (huge loss): (₹102 - ₹250) × 25 = -₹3,700
  Net Loss: -₹1,500 per set

For 2 Sets: -₹1,500 × 2 = -₹3,000

With Stop Loss + Re-Entries:
  Maximum Loss: -₹6,000 to -₹8,000 (if all re-entries also fail)
```

---

## Risk Warnings

### ⚠️ HIGH RISK STRATEGY - FOR EXPERIENCED TRADERS ONLY

This strategy involves selling options, which carries significant risk. Please review the following warnings carefully:

### 1. **Unlimited Loss Potential**
- Short call options have theoretically **unlimited risk** (NIFTY can rise indefinitely)
- Short put options have **limited but substantial risk** (NIFTY can fall to zero)
- Stop losses provide protection but are not guaranteed (gaps can occur)

### 2. **Margin Call Risk**
- Adverse market moves can trigger **margin calls** requiring immediate capital infusion
- Failure to meet margin calls can result in **forced liquidation** at unfavorable prices
- Margin requirements can increase suddenly during volatile periods

### 3. **Gap Risk (Overnight Holding)**
- Strategy holds positions **overnight**, exposing to gap up/down risk
- Markets can open significantly different from previous close
- **Weekend positions** (Friday → Monday) carry additional 48-hour gap risk
- Global events, earnings surprises, geopolitical events can cause large gaps

### 4. **Event Risk**
- **Economic announcements:** RBI policy, GDP, inflation data
- **Global events:** Fed decisions, geopolitical tensions, natural disasters
- **Corporate actions:** Index constituent changes, large corporate events
- **Technical disruptions:** Exchange outages, broker system failures

### 5. **Liquidity Risk**
- During extreme volatility, **bid-ask spreads widen significantly**
- Exit orders may execute at prices far from expected levels (**slippage**)
- Market depth may be insufficient for large positions
- Stop loss orders may not fill at desired prices

### 6. **Execution Risk**
- Orders may get **rejected** due to RMS limits, margin shortfall, or exchange errors
- **Partial fills** can leave positions unhedged
- **Time priority** at 9:19 AM entry may affect fill prices
- Re-entry logic adds complexity and execution uncertainty

### 7. **Non-Expiry Execution Risk**
- Strategy avoids expiry day but still holds **positional risk**
- Weekly options may have different dynamics than monthly options
- Liquidity may vary on non-expiry days
- Theta decay less predictable on non-expiry days

### 8. **Regulatory & Broker-Specific Risks**
- Position limits may restrict execution
- Broker risk management systems may prevent trades
- Regulatory changes can affect margin requirements
- Tax implications on options income

### 9. **Psychological Risk**
- Watching overnight positions can cause stress
- Emotion-driven decision making during volatile periods
- Overtrading or revenge trading after losses
- Difficulty sticking to stop loss discipline

### 10. **Capital Loss Risk**
- Possible to lose **entire allocated capital** in extreme scenarios
- Multiple consecutive losses can deplete capital rapidly
- Recovery from large drawdowns is mathematically difficult

---

## Mock Testing Plan

### Phase 1: Paper Trading (2 Weeks - Mandatory)

**Objective:** Validate strategy logic without real capital

**Activities:**
1. **Manual Paper Trading:**
   - Track NIFTY premium at 9:19 AM daily
   - Select CE/PE strikes closest to ₹100 premium
   - Note entry prices and calculate credit received
   - Monitor overnight and record exit prices at 9:18 AM next day
   - Calculate theoretical P&L for each trade

2. **Data Collection:**
   - Record 10 consecutive trade entries/exits
   - Document any expiry day exclusions
   - Track stop loss triggers (if price hits ₹entry + 20)
   - Note wait-and-trade triggers (if NIFTY moves >6%)

3. **Validation Checklist:**
   - [ ] Strike selection algorithm accurate (closest to ₹100)
   - [ ] Entry time precision (exactly 9:19:00 AM)
   - [ ] Exit time precision (exactly 9:18:00 AM next day)
   - [ ] Non-expiry filter working correctly
   - [ ] Stop loss calculations correct
   - [ ] Weekend rollover handling (Fri → Mon)

**Expected Outcomes:**
- 10 paper trades documented with P&L
- Strike selection accuracy verified
- Timing precision confirmed
- Risk parameters validated

### Phase 2: Single Set Live Testing (2 Weeks - Broker Integration)

**Objective:** Test real execution with minimal capital

**Configuration:**
```python
Capital: ₹2,00,000 (1 set only)
Lots: 1 lot per leg (25 units)
Duration: 10 trading days
Risk: Limited to 1 set for testing
```

**Activities:**
1. **Broker API Integration:**
   - Test order placement via API at 9:19 AM
   - Verify order execution and fill confirmations
   - Test stop loss order placement
   - Validate exit order execution next day at 9:18 AM

2. **System Monitoring:**
   - Monitor API logs for errors
   - Check order status updates
   - Verify margin deduction/release
   - Test re-entry logic if stop loss triggered

3. **Performance Tracking:**
   - Record actual P&L vs paper trading projections
   - Measure slippage (expected vs actual fill prices)
   - Document any execution failures or errors
   - Calculate actual margin requirements

**Validation Checklist:**
- [ ] Order placement successful at entry time
- [ ] Strike selection matches paper trading logic
- [ ] Fill prices within acceptable slippage range (±1-2 points)
- [ ] Stop loss orders placed correctly
- [ ] Exit orders execute on time next day
- [ ] Margin requirements match projections
- [ ] API rate limits not breached
- [ ] Error handling works as expected

**Expected Outcomes:**
- 10 real trades executed successfully
- Slippage measured and acceptable (<2% of premium)
- Margin requirements confirmed
- API integration validated

### Phase 3: Full Capital Deployment (After Phase 2 Sign-Off)

**Objective:** Scale to full capital with 2 sets

**Configuration:**
```python
Capital: ₹4,00,000 (2 sets)
Lots: 2 lots total (1 per set)
Duration: Ongoing production
Risk: Full strategy deployment
```

**Monitoring:**
- Daily P&L tracking
- Weekly performance review
- Monthly reconciliation with projections
- Adjust parameters based on live performance

---

## Testing Checklist for Partners

### Pre-Deployment Validation

#### **Broker Integration Tests**
- [ ] API connectivity established and stable
- [ ] Order placement tested during market hours
- [ ] Order cancellation functionality verified
- [ ] Position query API working correctly
- [ ] Margin query API returning accurate data
- [ ] Error handling for API failures tested

#### **Entry Logic Validation**
- [ ] Entry time precision verified (9:19:00 AM)
- [ ] Strike selection algorithm tested (closest to ₹100 premium)
- [ ] Order quantity correct (lots × 25 units per leg)
- [ ] Both legs execute simultaneously or within 5 seconds
- [ ] Market order execution tested (slippage measured)
- [ ] Wait-and-trade trigger tested (6% NIFTY move)

#### **Exit Logic Validation**
- [ ] Exit time precision verified (9:18:00 AM next day)
- [ ] Weekend rollover tested (Friday → Monday)
- [ ] Exit orders execute for both legs
- [ ] P&L calculation accurate
- [ ] Position closure confirmed in broker system

#### **Risk Management Validation**
- [ ] Stop loss placement tested (entry premium + 20 points)
- [ ] Stop loss trigger working correctly
- [ ] Re-entry logic tested (up to 2 additional entries)
- [ ] Re-entry capital availability verified
- [ ] Maximum loss per trade within limits (₹6,000)

#### **Non-Expiry Filter Validation**
- [ ] Expiry day detection working correctly
- [ ] Strategy skips execution on expiry days
- [ ] Calendar integration accurate for monthly expiry
- [ ] Manual override process tested (if needed)

#### **Capital & Margin Tests**
- [ ] Initial margin requirements measured (₹1,00,000 per set)
- [ ] Buffer capital available for re-entries
- [ ] Margin calls never triggered during testing
- [ ] Margin benefit for straddle confirmed with broker
- [ ] Peak margin requirements measured (₹1,50,000+)

#### **System Reliability Tests**
- [ ] Order placement at peak load (9:15-9:30 AM)
- [ ] API rate limits not breached
- [ ] Failover mechanism tested (if primary API fails)
- [ ] Emergency exit procedure documented and tested
- [ ] Manual override capability verified

### Risk Management Validation

#### **Position Limits**
- [ ] Maximum position size within regulatory limits (NIFTY options)
- [ ] Broker position limits confirmed (not near ceiling)
- [ ] Client-level position limits checked
- [ ] Exchange position limits reviewed

#### **Loss Controls**
- [ ] Daily loss limit circuit breaker tested
- [ ] Weekly loss limit alert configured
- [ ] Monthly drawdown threshold set (₹6,000)
- [ ] Auto-disable strategy on threshold breach

#### **Emergency Procedures**
- [ ] Emergency exit hotline established
- [ ] Manual exit procedure documented (if automated fails)
- [ ] Broker support contact information verified
- [ ] Escalation matrix defined (technical vs risk issues)

### Compliance Checks

#### **Regulatory Compliance**
- [ ] Strategy approved by internal risk management
- [ ] Client suitability assessment completed
- [ ] Risk disclosures signed by client
- [ ] Position reporting requirements met
- [ ] Tax implications disclosed to client

#### **Broker Compliance**
- [ ] Margin policies align with broker requirements
- [ ] Position limits within broker's RMS rules
- [ ] Overnight holding approved by broker
- [ ] Short options trading enabled for account

#### **Documentation**
- [ ] Strategy document reviewed and signed
- [ ] Execution agreement signed
- [ ] Risk acknowledgment form signed
- [ ] Emergency contact form completed
- [ ] Audit trail mechanism established

---

## Technical Implementation Details

### Code Architecture

**Base Class:** `NiftySTBT100Basket`

```python
Strategy Configuration:
  Basket ID: [Generated UUID]
  Basket Name: "STBT100"
  Capital: ₹4,00,000
  Enabled: True/False toggle

Strategy Cloning:
  - Base strategy (S1) defined with all parameters
  - Cloned for each weekday (MON, TUE, WED, THU, FRI)
  - Each clone operates independently
  - Set ID: 0 (default configuration)

Lot Configuration:
  - Dynamic lot sizing via `sets` parameter
  - Formula: lots = sets × 1 (1 lot per set)
  - Scalable from 1 set (₹2,00,000) to N sets
```

### Strategy Parameters

```python
Entry Configuration:
  entry_time: Time(hour=9, minute=19, sec=0, day='MON')
  # Separate entry time for each weekday instance

Exit Configuration:
  exit_time: [Time(hour=9, minute=18, sec=0, day='MON-FRI')]
  # Array of exit times covering all weekdays
  strategy_exit_type: StrategyType.ExitNextDay

Product & Execution:
  product: ProductType.Positional (NRML)
  is_intra_day: False
  execution_days: ExecutionDays.NonExpiry
```

### Leg Configuration

```python
Leg 1 (Call):
  leg_no: 1
  lots: -1 (negative indicates short/sell)
  transaction_type: TransactionType.Sell
  leg_type: LegType.CE
  index: Index.Nifty
  entry_by: LegEntry.get_entry_by_closest_premium(premium=100)
  stop_loss: LegStopLoss.get_stop_loss_by_points(points=20)
  re_cost: LegReCost.get_re_cost(entries=2)
  save_cancelled_order: False
  wait_and_trade: LegWaitAndTrade.get_trigger_by_percentage(percentage=6)

Leg 2 (Put):
  # Identical configuration except leg_type: LegType.PE
```

### Multi-User Support

```python
User Basket Association:
  - Base basket created with all strategies
  - Deep copied for each user
  - User-specific lot sizing applied
  - Associated to user's basket collection

Configuration Method:
  basket.configure_strategy_with_lots(
    sid='S1',
    base_basket=base_basket,
    index=Index.Nifty,
    lots=sets,  # User-defined sets (1, 2, 3, ...)
    entry_day=day  # MON/TUE/WED/THU/FRI
  )
```

### Database Schema Mapping

**Strategy Table Fields:**
```
strategy_id: 'S1'
strategy_name: 'STBT100'
entry_time: '09:19:00'
exit_time: '09:18:00'
product: 'Positional'
is_intra_day: False
execution_days: 'NonExpiry'
strategy_exit_type: 'ExitNextDay'
entry_day: 'MON'|'TUE'|'WED'|'THU'|'FRI'
```

**Leg Table Fields:**
```
leg_no: 1|2
lots: -1 (short position)
transaction_type: 'Sell'
leg_type: 'CE'|'PE'
index: 'Nifty'
entry_method: 'CLOSEST_PREMIUM'
premium_target: 100
stop_loss_points: 20
re_entry_count: 2
wait_trade_percentage: 6
```

---

## Approval Requirements

### Partner Sign-Off Checklist

**Risk Management Approval:**
- [ ] Strategy reviewed by risk committee
- [ ] Position limits approved
- [ ] Stop loss parameters acceptable
- [ ] Drawdown limits within tolerance
- [ ] Capital allocation approved
- [ ] Overnight risk acknowledged

**Compliance Sign-Off:**
- [ ] Regulatory requirements reviewed
- [ ] Client suitability confirmed
- [ ] Risk disclosures adequate
- [ ] Position reporting compliant
- [ ] Margin policies compliant
- [ ] Tax implications disclosed

**Technology Approval:**
- [ ] API integration tested and stable
- [ ] Execution precision verified (9:19 AM / 9:18 AM)
- [ ] Error handling adequate
- [ ] Monitoring systems in place
- [ ] Audit logging enabled
- [ ] Disaster recovery tested

**Operations Approval:**
- [ ] Broker account setup complete
- [ ] Margin funding arranged
- [ ] Emergency procedures documented
- [ ] Support team trained
- [ ] Escalation matrix defined
- [ ] Client communication plan ready

### Platform Deliverables

**Execution Reports:**
- [ ] Daily trade confirmations
- [ ] Order placement logs with timestamps
- [ ] Fill price documentation
- [ ] Stop loss trigger alerts
- [ ] Re-entry execution logs
- [ ] Exit execution confirmations

**Performance Reports:**
- [ ] Daily P&L summary
- [ ] Weekly performance review
- [ ] Monthly reconciliation report
- [ ] Slippage analysis report
- [ ] Margin utilization tracking
- [ ] Win rate and R:R tracking

**Technical Documentation:**
- [ ] API integration guide
- [ ] Error code reference
- [ ] Troubleshooting guide
- [ ] Emergency exit procedures
- [ ] System architecture diagram
- [ ] Data flow documentation

**Compliance Documentation:**
- [ ] Audit trail for all orders
- [ ] Position reporting files
- [ ] Risk event documentation
- [ ] Client communication logs
- [ ] Regulatory filings (if required)

---

## Contact Information

### Strategy Owner
**Organization:** [Your Trading Firm Name]
**Contact Person:** [Strategy Manager Name]
**Email:** [strategy@yourfirm.com]
**Phone:** [+91-XXXX-XXXXXX]

### Platform Support
**Technical Support:** [support@platform.com]
**API Issues:** [api-support@platform.com]
**Documentation:** [docs.platform.com/nifty-stbt]
**Support Hours:** Monday-Friday, 9:00 AM - 6:00 PM IST

### Risk Management
**Risk Team:** [risk@yourfirm.com]
**Escalation Hotline:** [+91-XXXX-XXXXXX]
**After-Hours Risk Contact:** [+91-XXXX-XXXXXX]

### Emergency Contacts
**24/7 Trading Desk:** [+91-XXXX-XXXXXX]
**Broker Support:** [broker-support@broker.com]
**Exchange Connectivity Issues:** [NSE helpdesk number]
**Emergency Exit Protocol:** [Document link or phone tree]

---

## Appendix

### Glossary of Terms

- **NIFTY:** NSE's benchmark index comprising 50 large-cap stocks
- **Straddle:** Simultaneous selling of Call and Put at same or different strikes
- **Positional:** Multi-day trade (overnight holding) using NRML margin
- **NRML:** Normal margin product (lower leverage, suitable for overnight)
- **Premium:** Price of an option contract
- **Stop Loss:** Predetermined exit level to limit losses
- **Re-Entry (Re-Cost):** Re-entering position after stop loss to average cost
- **Wait & Trade:** Conditional entry based on market movement threshold
- **Theta Decay:** Time value erosion of options (benefits option sellers)
- **Slippage:** Difference between expected and actual fill price

### Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | Oct 11, 2025 | Initial document for partner review | [Author Name] |

### Disclaimers

**Market Risk Disclosure:**
This strategy involves substantial risk of loss and is not suitable for all investors. Past performance is not indicative of future results. Options trading involves risk and is not suitable for all investors. Before trading, clients should read the relevant risk disclosure statements available on NSE/BSE websites.

**No Guarantee of Profit:**
The expected performance metrics are projections based on historical analysis and assumptions. Actual results may vary significantly. There is no guarantee of profit, and losses can exceed initial capital in extreme scenarios.

**Independent Advice:**
This document is for informational purposes only and does not constitute investment advice. Partners should conduct independent due diligence and consult with their own legal, financial, and compliance advisors before approving this strategy for deployment.

**Regulatory Compliance:**
Partners are responsible for ensuring compliance with all applicable laws, regulations, and exchange rules in their jurisdictions. This strategy has not been reviewed or approved by any regulatory authority.

---

**END OF DOCUMENT**

For questions or clarifications, please contact the strategy owner using the contact information provided above.
