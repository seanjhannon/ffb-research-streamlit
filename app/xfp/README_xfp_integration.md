# xFP Model - Production Integration Guide

This document provides everything needed to integrate the expected fantasy points (xFP) model into your Streamlit fantasy football application.

## 📦 What You're Getting

### Production Model Files
- **`xfp_model.pkl`** - Serialized trained model (2.9MB)
- **`xfp_deployment.py`** - Lightweight deployment module
- **`README.md`** - This integration guide

### Model Specifications
- **Training Data**: 2015-2024 (10 years, 483,605 plays)
- **Context Groups**: 34,940 unique game situations
- **Field Tolerance**: 1 yard (optimal balance)
- **Distance Tolerance**: 1 yard
- **Scoring Formats**: Standard, PPR, Half-PPR

## 🚀 Quick Integration

### 1. Copy Files to Your App
```bash
# Copy these files to your Streamlit app directory
cp xfp_model.pkl /path/to/your/app/
cp xfp_deployment.py /path/to/your/app/
```

### 2. Install Dependencies
```bash
pip install pandas numpy nfl-data-py
```

### 3. Basic Usage
```python
from xfp_deployment import load_xfp_model

# Load model once (cache it!)
@st.cache_resource
def load_model():
    return load_xfp_model()

xfp_calc = load_model()

# Calculate xFP for any play
expected_fp = xfp_calc.calculate_play_xfp(play_row, 'ppr')
```

## 📊 Model Performance

### Overall Performance
- **Correlation**: 0.966+ (excellent!)
- **Mean Absolute Error**: ~24-25 FP
- **Coverage**: 100% (all plays get predictions)
- **Bias**: Minimal (well-calibrated)

### By Opportunity Type
- **Rush Attempts**: 0.30+ correlation
- **Targets**: 0.20+ correlation  
- **Pass Attempts**: 0.18+ correlation
- **Scrambles**: 0.26+ correlation

## 🎯 Streamlit Integration Examples

### 1. Player xFP Dashboard
```python
import streamlit as st
from xfp_deployment import load_xfp_model, calculate_player_efficiency

@st.cache_resource
def load_model():
    return load_xfp_model()

xfp_calc = load_model()

# Player selection
player = st.selectbox("Select Player", player_list)
scoring_format = st.selectbox("Scoring Format", ['standard', 'ppr', 'half_ppr'])

# Calculate efficiency
player_data = get_player_plays(player)  # Your function
metrics = calculate_player_efficiency(player_data, player, scoring_format)

# Display metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Expected FP", f"{metrics['expected_fp']:.1f}")
with col2:
    st.metric("Actual FP", f"{metrics['actual_fp']:.1f}")
with col3:
    st.metric("Efficiency", f"{metrics['efficiency']:.3f}")
```

### 2. Play-by-Play Analysis
```python
# For each play in your data
for _, play in plays_df.iterrows():
    expected_fp = xfp_calc.calculate_play_xfp(play, scoring_format)
    
    # Add to your dataframe
    plays_df.loc[play.name, 'expected_fp'] = expected_fp
    plays_df.loc[play.name, 'efficiency'] = play['actual_fp'] / expected_fp
```

### 3. Trade Analyzer
```python
def analyze_trade(player_a, player_b, scoring_format):
    """Compare two players using xFP"""
    
    # Get player data (your function)
    data_a = get_player_data(player_a)
    data_b = get_player_data(player_b)
    
    # Calculate xFP
    xfp_a = sum(xfp_calc.calculate_play_xfp(play, scoring_format) for _, play in data_a.iterrows())
    xfp_b = sum(xfp_calc.calculate_play_xfp(play, scoring_format) for _, play in data_b.iterrows())
    
    # Calculate actual FP
    actual_a = data_a['actual_fp'].sum()
    actual_b = data_b['actual_fp'].sum()
    
    return {
        'player_a': {'expected': xfp_a, 'actual': actual_a, 'efficiency': actual_a/xfp_a},
        'player_b': {'expected': xfp_b, 'actual': actual_b, 'efficiency': actual_b/xfp_b}
    }
```

## 🔧 Advanced Usage

### Custom Player Analysis
```python
def get_player_xfp_breakdown(player_id, season_data, scoring_format='ppr'):
    """Get detailed xFP breakdown for a player"""
    
    xfp_calc = load_xfp_model()
    
    # Filter player's plays
    player_plays = season_data[season_data['player_id'] == player_id]
    
    results = []
    for _, play in player_plays.iterrows():
        expected_fp = xfp_calc.calculate_play_xfp(play, scoring_format)
        
        results.append({
            'play_id': play['play_id'],
            'expected_fp': expected_fp,
            'actual_fp': calculate_actual_fp(play),  # Your function
            'opportunity_type': determine_opportunity_type(play),  # Your function
            'context': f"{play['yardline_100']} yd line, {play['down']} & {play['ydstogo']}"
        })
    
    return pd.DataFrame(results)
```

### Batch Processing
```python
def calculate_season_xfp(season_data, scoring_format='ppr'):
    """Calculate xFP for entire season efficiently"""
    
    xfp_calc = load_xfp_model()
    
    # Process all plays
    season_data['expected_fp'] = season_data.apply(
        lambda row: xfp_calc.calculate_play_xfp(row, scoring_format), 
        axis=1
    )
    
    # Calculate efficiency
    season_data['efficiency'] = season_data['actual_fp'] / season_data['expected_fp']
    
    return season_data
```

## 📈 Key Metrics to Track

### Player-Level Metrics
- **Expected FP**: Total expected fantasy points
- **Actual FP**: Total actual fantasy points  
- **Efficiency**: Actual FP / Expected FP
- **Over/Under Performance**: Actual FP - Expected FP

### Opportunity-Level Metrics
- **Expected FP per Play**: Average expected value
- **Efficiency Distribution**: How often players exceed expectations
- **Context Analysis**: Performance by game situation

## ⚠️ Important Considerations

### Data Requirements
- Model expects specific column names from `nfl-data-py`
- Ensure your data has: `yardline_100`, `down`, `ydstogo`, `rush_attempt`, `pass_attempt`, etc.

### Performance
- Model loads in ~1-2 seconds
- Predictions are instant (< 1ms per play)
- Cache the model with `@st.cache_resource`

### Scoring Formats
- **Standard**: Yards × 0.1, TDs × 6, Fumbles × -2
- **PPR**: Standard + Receptions × 1
- **Half-PPR**: Standard + Receptions × 0.5

## 🔍 Troubleshooting

### Common Issues
1. **Import Error**: Make sure `xfp_deployment.py` is in your app directory
2. **Model Not Found**: Ensure `xfp_model.pkl` is in the same directory
3. **Column Errors**: Check that your data has required columns
4. **Memory Issues**: Use `@st.cache_resource` to cache the model

### Debugging
```python
# Check model info
xfp_calc = load_xfp_model()
model_info = xfp_calc.get_model_info()
print(f"Model status: {model_info['status']}")
print(f"Available formats: {xfp_calc.get_available_scoring_formats()}")

# Test a single prediction
sample_play = create_sample_play()  # Your function
expected_fp = xfp_calc.calculate_play_xfp(sample_play, 'ppr')
print(f"Expected FP: {expected_fp}")
```

## 🎉 Success Metrics

Your integration is working well if you see:
- **Model loads without errors**
- **Predictions return reasonable values** (0.1-10+ FP range)
- **Efficiency distributions** show realistic patterns
- **Player rankings** make sense relative to actual performance

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify your data format matches `nfl-data-py` structure
3. Test with sample data first
4. Check the model development README for technical details

---

**Happy analyzing!** 🚀

The xFP model will provide valuable insights into player opportunity and performance that go beyond traditional fantasy football statistics.
