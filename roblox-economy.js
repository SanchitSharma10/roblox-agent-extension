// This file should be saved as "roblox-economy.js" next to your app.py file

class RobloxEconomyApp {
  constructor() {
    this.supabase = null;
    this.currentData = [];
    this.debugMode = true;
    this.columnMapping = {}; // Will store the actual column names
    this.initialized = false; // Track initialization state for other components
    this.init();
  }

  async init() {
    this.log('🚀 Starting app initialization...');
    
    // Check if Supabase library is loaded
    if (typeof window.supabase === 'undefined') {
      this.log('❌ Supabase library not loaded');
      this.showError('Supabase library not loaded. Check internet connection.');
      return;
    }
    this.log('✅ Supabase library loaded');

    // Initialize Supabase connection
    await this.initSupabase();
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Load initial data
    if (this.supabase) {
      this.loadData();
    }
  }

  log(message) {
    if (this.debugMode) {
      console.log(message);
    }
  }

  async initSupabase() {
    try {
      this.log('🔗 Attempting Supabase connection...');
      
      // Your CORRECT Supabase credentials
      const supabaseUrl = 'https://gnlpztlwwinnkmunufgb.supabase.co';
      const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdubHB6dGx3d2lubmttdW51ZmdiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjA1NDk5OCwiZXhwIjoyMDYxNjMwOTk4fQ.w0TUqo9b5ggDyGh5hMM-ndE5Vr2UF2VNt3X4UdLqq6s';
      
      this.log(`📡 URL: ${supabaseUrl}`);
      this.log(`🔑 Key: ${supabaseKey.substring(0, 20)}...`);
      
      // Initialize Supabase client
      this.supabase = window.supabase.createClient(supabaseUrl, supabaseKey);
      this.log('✅ Supabase client created');
      
      // Test connection and discover column structure
      this.log('🧪 Testing connection and discovering table structure...');
      await this.discoverTableStructure();
      
      this.log('✅ Connection test successful');
      this.updateConnectionStatus(true);
      
    } catch (error) {
      this.log(`❌ Supabase initialization failed: ${error.message}`);
      this.log('Full error details:', error);
      this.updateConnectionStatus(false, error);
      this.showError(`Database connection failed: ${error.message}`);
    }
  }

  async discoverTableStructure() {
    // Try to get a sample record to understand the table structure
    const { data: sampleData, error: sampleError } = await this.supabase
      .from('marketplace_items')
      .select('*')
      .limit(1);
    
    if (sampleError) {
      this.log(`❌ Sample fetch failed: ${sampleError.message}`);
      throw sampleError;
    }
    
    if (sampleData && sampleData.length > 0) {
      const sample = sampleData[0];
      this.log('✅ Sample record found');
      this.log('Available columns:', Object.keys(sample));
      this.log('Sample data:', sample);
      
      // Create column mapping based on what's actually available
      this.columnMapping = this.createColumnMapping(Object.keys(sample));
      this.log('Column mapping:', this.columnMapping);
    } else {
      throw new Error('No data found in marketplace_items table');
    }
  }

  createColumnMapping(availableColumns) {
    const mapping = {};
    
    // Map price field
    const priceFields = ['recent_average_price', 'price', 'rolimons_value', 'value', 'rap'];
    mapping.price = priceFields.find(field => availableColumns.includes(field)) || 'price';
    
    // Map name field
    const nameFields = ['name', 'item_name', 'title'];
    mapping.name = nameFields.find(field => availableColumns.includes(field)) || 'name';
    
    // Map category field
    const categoryFields = ['type', 'category', 'asset_type', 'item_type'];
    mapping.category = categoryFields.find(field => availableColumns.includes(field)) || 'type';
    
    // Map creator field
    const creatorFields = ['creator_name', 'creator', 'creator_id'];
    mapping.creator = creatorFields.find(field => availableColumns.includes(field)) || 'creator_name';
    
    // Map sales field
    const salesFields = ['sales_count', 'sales', 'sale_count', 'transactions'];
    mapping.sales = salesFields.find(field => availableColumns.includes(field)) || 'sales_count';
    
    // Map price change field
    const priceChangeFields = ['price_change_percent', 'change_percent', 'price_change'];
    mapping.priceChange = priceChangeFields.find(field => availableColumns.includes(field)) || null;
    
    // Map ID field
    const idFields = ['id', 'item_id', 'asset_id'];
    mapping.id = idFields.find(field => availableColumns.includes(field)) || 'id';
    
    // Map RAP field
    const rapFields = ['rap', 'recent_average_price', 'average_price'];
    mapping.rap = rapFields.find(field => availableColumns.includes(field)) || mapping.price;
    
    return mapping;
  }

  updateConnectionStatus(connected, error = null) {
    let statusDiv = document.getElementById('connectionStatus');
    if (!statusDiv) {
      statusDiv = document.createElement('div');
      statusDiv.id = 'connectionStatus';
      statusDiv.style.cssText = 'position: fixed; top: 5px; right: 5px; padding: 5px 10px; border-radius: 4px; font-size: 12px; z-index: 1000; border: 1px solid #ccc;';
      document.body.appendChild(statusDiv);
    }
    
    if (connected) {
      statusDiv.innerHTML = '🟢 Database Connected';
      statusDiv.style.backgroundColor = '#e8f5e9';
      statusDiv.style.color = '#2e7d32';
      statusDiv.style.borderColor = '#4caf50';
    } else {
      statusDiv.innerHTML = '🔴 Database Error';
      statusDiv.style.backgroundColor = '#ffebee';
      statusDiv.style.color = '#c62828';
      statusDiv.style.borderColor = '#f44336';
      
      if (error) {
        statusDiv.title = error.message;
      }
    }
  }

  setupEventListeners() {
    document.getElementById('refreshBtn').addEventListener('click', () => {
      this.log('🔄 Refresh button clicked');
      this.loadData();
    });

    document.getElementById('categoryFilter').addEventListener('change', (e) => {
      this.filterAndDisplayData(e.target.value, document.getElementById('sortFilter').value);
    });

    document.getElementById('sortFilter').addEventListener('change', (e) => {
      this.filterAndDisplayData(document.getElementById('categoryFilter').value, e.target.value);
    });
  }

  async loadData() {
    try {
      this.log('📦 Starting data load...');
      this.showLoading();
      
      if (!this.supabase || !this.columnMapping) {
        throw new Error('Database connection or column mapping not initialized');
      }
      
      // Get marketplace items using discovered column structure
      this.log('📦 Fetching marketplace items...');
      
      // Build the order clause based on available fields
      let orderField = this.columnMapping.price;
      
      const { data: items, error: itemsError } = await this.supabase
        .from('marketplace_items')
        .select('*')
        .order(orderField, { ascending: false })
        .limit(200);

      if (itemsError) {
        this.log(`❌ Data fetch failed: ${itemsError.message}`);
        throw itemsError;
      }

      this.currentData = items || [];
      this.log(`✅ Loaded ${this.currentData.length} items from database`);
      
      if (this.currentData.length > 0) {
        this.log('Sample item:', this.currentData[0]);
      }
      
      // Update UI
      this.updateMetrics();
      this.populateCategoryFilter();
      this.filterAndDisplayData();
      
      // Mark as initialized
      this.initialized = true;
      
    } catch (error) {
      this.log(`❌ Error loading data: ${error.message}`);
      this.log('Full error:', error);
      this.showError(`Failed to load data: ${error.message}`);
      
      // If Supabase data fetch fails, try getting data from the WebSocket
      this.tryFallbackDataSource();
    }
  }
  
  tryFallbackDataSource() {
    this.log('⚠️ Trying to fall back to WebSocket data source');
    // If window.aiClient exists (from the WebSocket implementation)
    if (window.aiClient && typeof window.aiClient.submitQuery === 'function') {
      window.aiClient.submitQuery('Show marketplace overview');
    }
  }

  updateMetrics() {
    const data = this.currentData;
    
    // Calculate metrics using column mapping
    const totalItems = data.length;
    
    // Calculate total value using the mapped price field
    const priceField = this.columnMapping.price;
    const totalValue = data.reduce((sum, item) => {
      const price = item[priceField] || 0;
      return sum + price;
    }, 0);
    
    // Count unique categories using mapped category field
    const categoryField = this.columnMapping.category;
    const categories = new Set();
    data.forEach(item => {
      const category = item[categoryField];
      if (category && category !== 'Unknown') {
        categories.add(category);
      }
    });
    
    this.log(`Metrics: ${totalItems} items, ${totalValue} total value, ${categories.size} categories`);
    
    // Update UI
    document.getElementById('totalItems').textContent = totalItems.toLocaleString();
    document.getElementById('totalValue').textContent = this.formatNumber(totalValue);
    document.getElementById('activeCategories').textContent = categories.size;
  }

  getCategoryFromItem(item) {
    return item[this.columnMapping.category] || 'Unknown';
  }

  getPriceFromItem(item) {
    return item[this.columnMapping.price] || 0;
  }
  
  getRapFromItem(item) {
    return item[this.columnMapping.rap] || 0;
  }

  populateCategoryFilter() {
    const categoryFilter = document.getElementById('categoryFilter');
    
    // Keep the "All Categories" option
    const allOption = categoryFilter.querySelector('option[value=""]');
    categoryFilter.innerHTML = '';
    if (allOption) {
      categoryFilter.appendChild(allOption);
    } else {
      const option = document.createElement('option');
      option.value = '';
      option.textContent = 'All Categories';
      categoryFilter.appendChild(option);
    }
    
    // Get unique categories using mapped field
    const uniqueCategories = new Set();
    const categoryField = this.columnMapping.category;
    
    this.currentData.forEach(item => {
      const category = item[categoryField];
      if (category && category !== 'Unknown') {
        uniqueCategories.add(category);
      }
    });
    
    this.log(`Found categories: ${Array.from(uniqueCategories).join(', ')}`);
    
    // Sort and add to dropdown
    Array.from(uniqueCategories).sort().forEach(category => {
      const option = document.createElement('option');
      option.value = category;
      option.textContent = category;
      categoryFilter.appendChild(option);
    });
  }

  filterAndDisplayData(categoryFilter = '', sortFilter = 'price') {
    let filteredData = [...this.currentData];
    const categoryField = this.columnMapping.category;
    const priceField = this.columnMapping.price;
    const nameField = this.columnMapping.name;

    // Apply category filter
    if (categoryFilter) {
      filteredData = filteredData.filter(item => 
        item[categoryField] === categoryFilter
      );
    }

    // Apply sorting using mapped fields
    filteredData.sort((a, b) => {
      let aVal, bVal;
      
      switch (sortFilter) {
        case 'price':
          aVal = a[priceField] || 0;
          bVal = b[priceField] || 0;
          break;
        case 'name':
          aVal = a[nameField] || '';
          bVal = b[nameField] || '';
          return aVal.localeCompare(bVal);
        case 'demand':
          aVal = a.demand || 0;
          bVal = b.demand || 0;
          break;
        case 'rarity_score':
          aVal = a.rarity_score || 0;
          bVal = b.rarity_score || 0;
          break;
        case 'trend':
          // Sort by trend level and direction
          aVal = (a.trend || 0) * 10 + (a.trend_direction || 0);
          bVal = (b.trend || 0) * 10 + (b.trend_direction || 0);
          break;
        default:
          aVal = a[sortFilter] || 0;
          bVal = b[sortFilter] || 0;
      }

      if (sortFilter === 'name') {
        return aVal.localeCompare(bVal);
      }
      return bVal - aVal;
    });

    // Display data
    this.displayItems(filteredData.slice(0, 100));
  }

  displayItems(items) {
    const tbody = document.getElementById('itemsTableBody');
    
    if (items.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" class="loading">No items found</td></tr>';
      return;
    }
    
    // Use column mapping to access the correct fields
    const nameField = this.columnMapping.name;
    const categoryField = this.columnMapping.category;
    const priceField = this.columnMapping.price;
    const rapField = this.columnMapping.rap;
    const priceChangeField = this.columnMapping.priceChange;

    tbody.innerHTML = items.map(item => `
      <tr>
        <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" 
            title="${this.escapeHtml(item[nameField])}">
          ${this.escapeHtml(item[nameField] || 'Unknown')}
        </td>
        <td>${this.escapeHtml(item[categoryField] || 'Unknown')}</td>
        <td>${this.formatNumber(item[priceField] || 0)}</td>
        <td>${this.formatNumber(item[rapField] || 0)}</td>
        <td>${this.formatPriceChange(item[priceChangeField])}</td>
        <td>${this.formatTrend(item.trend, item.trend_direction)}</td>
        <td>${this.formatDemand(item.demand)}</td>
        <td>${this.formatRarity(item.rarity_score)}</td>
      </tr>
    `).join('');
  }

  formatNumber(num) {
    if (!num || num === 0) return '0';
    
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toLocaleString();
  }

  formatTrend(trendLevel, trendDirection) {
    if (!trendLevel || !trendDirection) {
      return '<span class="trend neutral">—</span>';
    }
    
    const direction = trendDirection > 0 ? '↗️' : trendDirection < 0 ? '↘️' : '→';
    const className = trendDirection > 0 ? 'positive' : trendDirection < 0 ? 'negative' : 'neutral';
    const strength = '●'.repeat(Math.min(trendLevel, 4));
    
    return `<span class="trend ${className}" title="Trend strength: ${trendLevel}/4">
              ${direction} ${strength}
            </span>`;
  }

  formatRarity(rarityScore) {
    if (!rarityScore) return '—';
    
    const stars = '★'.repeat(Math.min(rarityScore, 5));
    const className = rarityScore >= 4 ? 'legendary' : rarityScore >= 3 ? 'epic' : rarityScore >= 2 ? 'rare' : 'common';
    
    return `<span class="rarity ${className}" title="Rarity: ${rarityScore}/5">${stars}</span>`;
  }

  formatDemand(demand) {
    if (demand === null || demand === undefined) return '<span class="demand">—</span>';
    
    let className = 'low';
    let bars = '';
    
    // Convert demand to bars (0-5 scale)
    const demandLevel = Math.min(Math.max(parseInt(demand), 0), 5);
    bars = '█'.repeat(demandLevel) + '░'.repeat(5 - demandLevel);
    
    if (demandLevel >= 4) className = 'high';
    else if (demandLevel >= 2) className = 'medium';
    else className = 'low';
    
    return `<span class="demand ${className}" title="Demand: ${demandLevel}/5">${bars}</span>`;
  }

  formatPriceChange(percent) {
    if (percent === null || percent === undefined || percent === 0) {
      return '<span class="price-change neutral">--</span>';
    }
    
    const formatted = `${percent > 0 ? '+' : ''}${percent.toFixed(1)}%`;
    const className = percent > 0 ? 'positive' : 'negative';
    
    return `<span class="price-change ${className}">${formatted}</span>`;
  }

  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  showLoading() {
    const tbody = document.getElementById('itemsTableBody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="8" class="loading">Loading marketplace data...</td></tr>';
  }

  showError(message) {
    const tbody = document.getElementById('itemsTableBody');
    if (!tbody) return;
    tbody.innerHTML = `<tr><td colspan="8" class="error">${this.escapeHtml(message)}</td></tr>`;
  }
}