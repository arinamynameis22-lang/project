/**
 * Система управления продажами автомобилей — фронтенд.
 * Базовая структура: API-клиент, уведомления, форматирование, инициализация.
 */
(function () {
  'use strict';

  const API_BASE_URL = 'http://localhost:8000/api';

  /**
   * Выполнить fetch с обработкой ошибок. Возвращает JSON или выбрасывает исключение.
   */
  async function request(url, options = {}) {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
    if (!response.ok) {
      const text = await response.text();
      let detail = text;
      try {
        const json = JSON.parse(text);
        detail = json.detail || (Array.isArray(json.detail) ? json.detail.map(d => d.msg || d).join(', ') : text);
      } catch (_) {}
      throw new Error(detail);
    }
    if (response.status === 204 || response.headers.get('content-length') === '0') {
      return null;
    }
    return response.json();
  }

  const API = {
    async fetchCars(status = null, skip = 0, limit = 100) {
      const params = new URLSearchParams({ skip, limit });
      if (status) params.set('status', status);
      return request(`${API_BASE_URL}/cars?${params}`);
    },

    async fetchCarById(id) {
      return request(`${API_BASE_URL}/cars/${id}`);
    },

    async fetchCarByVin(vin) {
      return request(`${API_BASE_URL}/cars/vin/${encodeURIComponent(vin)}`);
    },

    async createCar(carData) {
      return request(`${API_BASE_URL}/cars`, {
        method: 'POST',
        body: JSON.stringify(carData),
      });
    },

    async updateCar(id, carData) {
      return request(`${API_BASE_URL}/cars/${id}`, {
        method: 'PUT',
        body: JSON.stringify(carData),
      });
    },

    async deleteCar(id) {
      return request(`${API_BASE_URL}/cars/${id}`, { method: 'DELETE' });
    },

    async createMovement(movementData) {
      return request(`${API_BASE_URL}/movements`, {
        method: 'POST',
        body: JSON.stringify(movementData),
      });
    },

    async fetchMovements(skip = 0, limit = 100) {
      return request(`${API_BASE_URL}/movements?skip=${skip}&limit=${limit}`);
    },

    async fetchMovementsByCarId(carId) {
      return request(`${API_BASE_URL}/movements/car/${carId}`);
    },

    async sellCar(saleData) {
      return request(`${API_BASE_URL}/sales`, {
        method: 'POST',
        body: JSON.stringify(saleData),
      });
    },

    async fetchSales(startDate = null, endDate = null) {
      const params = new URLSearchParams();
      if (startDate) params.set('start_date', startDate);
      if (endDate) params.set('end_date', endDate);
      const q = params.toString() ? '?' + params.toString() : '';
      return request(`${API_BASE_URL}/sales${q}`);
    },

    async fetchReportSales(startDate = null, endDate = null) {
      const params = new URLSearchParams();
      if (startDate) params.set('start_date', startDate);
      if (endDate) params.set('end_date', endDate);
      const q = params.toString() ? '?' + params.toString() : '';
      return request(`${API_BASE_URL}/reports/sales${q}`);
    },

    async fetchReportStock() {
      return request(`${API_BASE_URL}/reports/stock`);
    },

    async fetchReportBuyers() {
      return request(`${API_BASE_URL}/reports/buyers`);
    },

    async fetchReportOperations(skip = 0, limit = 100, operationType = null) {
      const params = new URLSearchParams({ skip, limit });
      if (operationType) params.set('operation_type', operationType);
      return request(`${API_BASE_URL}/reports/operations?${params}`);
    },

    async uploadFile(file, fileType) {
      const formData = new FormData();
      formData.append('file', file);
      const endpoint = fileType === 'auto' ? 'auto' : fileType;
      const response = await fetch(`${API_BASE_URL}/files/upload/${endpoint}`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        const text = await response.text();
        let detail = text;
        try {
          const json = JSON.parse(text);
          detail = json.detail || text;
        } catch (_) {}
        throw new Error(detail);
      }
      return response.json();
    },
  };

  window.API = API;

  /**
   * Показать уведомление (success, error, info).
   */
  function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationContainer');
    if (!container) {
      const div = document.createElement('div');
      div.id = 'notificationContainer';
      div.className = 'position-fixed top-0 end-0 p-3';
      div.style.zIndex = '9999';
      document.body.appendChild(div);
    }
    const box = document.getElementById('notificationContainer');
    const alertClass = type === 'success' ? 'alert-success' : type === 'error' ? 'alert-danger' : 'alert-info';
    const el = document.createElement('div');
    el.className = `alert ${alertClass} alert-dismissible fade show shadow`;
    el.setAttribute('role', 'alert');
    el.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    box.appendChild(el);
    setTimeout(() => {
      if (el.parentNode) el.remove();
    }, 5000);
  }

  window.showNotification = showNotification;

  /**
   * Форматирование суммы в рубли.
   */
  function formatCurrency(amount) {
    if (amount == null || isNaN(amount)) return '—';
    return new Intl.NumberFormat('ru-RU', {
      style: 'decimal',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount) + ' ₽';
  }

  window.formatCurrency = formatCurrency;

  function statusBadgeClass(status) {
    if (!status) return 'status-badge';
    if (status === 'на складе') return 'status-badge status-stock';
    if (status === 'продан') return 'status-badge status-sold';
    if (status === 'в демозале') return 'status-badge status-demo';
    if (status === 'на сервисе') return 'status-badge status-service';
    return 'status-badge';
  }

  function formatDate(dateStr) {
    if (!dateStr) return '—';
    try {
      const d = new Date(dateStr);
      return isNaN(d.getTime()) ? dateStr : d.toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' });
    } catch (_) {
      return dateStr;
    }
  }

  function renderCarsTable(cars) {
    const tbody = document.getElementById('carsTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (!cars || cars.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" class="text-muted text-center">Нет данных</td></tr>';
      return;
    }
    cars.forEach(function (car) {
      const statusClass = statusBadgeClass(car.status);
      const canMove = car.status !== 'продан';
      const canSell = car.status !== 'продан';
      const row = document.createElement('tr');
      row.innerHTML =
        '<td>' + escapeHtml(car.vin) + '</td>' +
        '<td>' + escapeHtml(car.model) + '</td>' +
        '<td>' + escapeHtml(car.color) + '</td>' +
        '<td class="text-price">' + formatCurrency(car.purchase_price) + '</td>' +
        '<td class="text-price">' + formatCurrency(car.sale_price) + '</td>' +
        '<td><span class="' + statusClass + '" data-status="' + escapeHtml(car.status) + '">' + escapeHtml(car.status) + '</span></td>' +
        '<td>' + escapeHtml(car.location) + '</td>' +
        '<td>' +
        '<button type="button" class="btn btn-sm btn-outline-primary me-1" data-action="view" data-car-id="' + car.id + '">Просмотр</button>' +
        (canMove ? '<button type="button" class="btn btn-sm btn-outline-secondary me-1" data-action="move" data-car-vin="' + escapeHtml(car.vin) + '">Переместить</button>' : '') +
        (canSell ? '<button type="button" class="btn btn-sm btn-outline-success me-1" data-action="sell" data-car-vin="' + escapeHtml(car.vin) + '">Продать</button>' : '') +
        '<button type="button" class="btn btn-sm btn-outline-danger" data-action="delete" data-car-id="' + car.id + '" data-car-vin="' + escapeHtml(car.vin) + '">Удалить</button>' +
        '</td>';
      tbody.appendChild(row);
    });
  }

  function escapeHtml(text) {
    if (text == null) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function bindCarsTableActions() {
    const tbody = document.getElementById('carsTableBody');
    if (!tbody) return;
    tbody.addEventListener('click', function (e) {
      const btn = e.target.closest('[data-action]');
      if (!btn) return;
      const action = btn.getAttribute('data-action');
      const id = btn.getAttribute('data-car-id');
      const vin = btn.getAttribute('data-car-vin');
      if (action === 'view' && id) {
        API.fetchCarById(id).then(function (car) {
          showNotification('Автомобиль: ' + car.model + ', VIN ' + car.vin + ', статус ' + car.status, 'info');
        }).catch(function (err) { showNotification(err.message, 'error'); });
      } else if (action === 'move' && vin) {
        document.getElementById('movementVin').value = vin;
        document.querySelector('[data-bs-target="#movements"]').click();
      } else if (action === 'sell' && vin) {
        document.getElementById('saleVin').value = vin;
        document.querySelector('[data-bs-target="#sales"]').click();
      } else if (action === 'delete' && id && vin) {
        if (!confirm('Удалить автомобиль ' + vin + '?')) return;
        API.deleteCar(id).then(function () {
          showNotification('Автомобиль удалён', 'success');
          loadCarsTab();
        }).catch(function (err) { showNotification(err.message, 'error'); });
      }
    });
  }

  function renderMovementsTable(movements) {
    const tbody = document.getElementById('movementsTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (!movements || movements.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="text-muted text-center">Нет данных</td></tr>';
      return;
    }
    movements.forEach(function (m) {
      const row = document.createElement('tr');
      row.innerHTML =
        '<td>' + formatDate(m.date) + '</td>' +
        '<td>' + escapeHtml(m.vin != null ? m.vin : '#' + m.car_id) + '</td>' +
        '<td>' + escapeHtml(m.from_location) + '</td>' +
        '<td>' + escapeHtml(m.to_location) + '</td>';
      tbody.appendChild(row);
    });
  }

  function renderSalesTable(sales) {
    const tbody = document.getElementById('salesTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (!sales || sales.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="text-muted text-center">Нет данных</td></tr>';
      return;
    }
    sales.forEach(function (car) {
      const row = document.createElement('tr');
      row.innerHTML =
        '<td>' + escapeHtml(car.vin) + '</td>' +
        '<td>' + escapeHtml(car.model) + '</td>' +
        '<td class="text-price">' + formatCurrency(car.sale_price) + '</td>' +
        '<td>' + (car.buyer_id != null ? 'ID ' + car.buyer_id : '—') + '</td>';
      tbody.appendChild(row);
    });
  }

  function renderReport(reportData, reportType) {
    const el = document.getElementById('reportOutput');
    if (!el) return;
    if (!reportData) {
      el.textContent = 'Нет данных';
      return;
    }
    if (reportType === 'sales') {
      const p = reportData.period || {};
      let html = '<div class="card mb-3"><div class="card-header">Период</div><div class="card-body">' +
        (p.start || '—') + ' — ' + (p.end || '—') + '</div></div>';
      html += '<div class="card mb-3"><div class="card-header">Итого</div><div class="card-body">' +
        'Продано: ' + (reportData.total_count || 0) + ' авто<br>' +
        'Сумма продаж: ' + formatCurrency(reportData.total_sales) + '<br>' +
        'Прибыль: ' + formatCurrency(reportData.total_profit) + '<br>' +
        'Средняя цена: ' + formatCurrency(reportData.average_price) + '</div></div>';
      if (reportData.by_model && reportData.by_model.length) {
        html += '<div class="card"><div class="card-header">По моделям</div><div class="card-body"><ul class="list-group list-group-flush">';
        reportData.by_model.forEach(function (item) {
          html += '<li class="list-group-item d-flex justify-content-between">' +
            '<span>' + escapeHtml(item.model) + '</span>' +
            '<span>' + item.count + ' шт., ' + formatCurrency(item.total) + ', прибыль ' + formatCurrency(item.profit) + '</span></li>';
        });
        html += '</ul></div></div>';
      }
      el.innerHTML = html;
    } else if (reportType === 'stock') {
      let html = '<div class="card mb-3"><div class="card-header">Остатки</div><div class="card-body">' +
        'Всего: ' + (reportData.total_count || 0) + ' авто, стоимость ' + formatCurrency(reportData.total_value) + '</div></div>';
      if (reportData.by_model && reportData.by_model.length) {
        reportData.by_model.forEach(function (modelBlock) {
          html += '<div class="card mb-2"><div class="card-header">' + escapeHtml(modelBlock.model) + ' — ' + modelBlock.count + ' шт.</div><div class="card-body">';
          if (modelBlock.by_color && modelBlock.by_color.length) {
            modelBlock.by_color.forEach(function (colorBlock) {
              html += '<p class="mb-1"><strong>' + escapeHtml(colorBlock.color) + '</strong>: ' + colorBlock.count + ' шт.</p>';
              if (colorBlock.cars && colorBlock.cars.length) {
                html += '<small class="text-muted">' + colorBlock.cars.map(function (c) { return c.vin; }).join(', ') + '</small>';
              }
            });
          }
          html += '</div></div>';
        });
      }
      el.innerHTML = html;
    } else if (reportType === 'buyers') {
      let html = '<div class="card mb-3"><div class="card-header">Покупатели</div><div class="card-body">Всего: ' + (reportData.total_buyers || 0) + '</div></div>';
      if (reportData.buyers && reportData.buyers.length) {
        reportData.buyers.forEach(function (b) {
          html += '<div class="card mb-2"><div class="card-header">' + escapeHtml(b.name) + '</div><div class="card-body">' +
            'Покупок: ' + b.purchases_count + ', на сумму ' + formatCurrency(b.total_spent) + '<br>';
          if (b.cars && b.cars.length) {
            html += '<ul class="mb-0">' + b.cars.map(function (c) {
              return '<li>' + escapeHtml(c.model) + ' (' + escapeHtml(c.color) + ') — ' + formatCurrency(c.sale_price) + '</li>';
            }).join('') + '</ul>';
          }
          html += '</div></div>';
        });
      }
      el.innerHTML = html;
    } else if (reportType === 'operations') {
      if (Array.isArray(reportData) && reportData.length) {
        let html = '<ul class="list-group">';
        reportData.forEach(function (op) {
          html += '<li class="list-group-item">' + formatDate(op.date) + ' — ' + escapeHtml(op.operation_type) + (op.details ? ': ' + escapeHtml(op.details) : '') + '</li>';
        });
        html += '</ul>';
        el.innerHTML = html;
      } else {
        el.textContent = 'Нет операций';
      }
    } else {
      el.textContent = JSON.stringify(reportData, null, 2);
    }
  }

  function loadCarsTab() {
    const status = document.getElementById('carsFilterStatus');
    const value = status ? status.value || null : null;
    API.fetchCars(value)
      .then(function (data) { renderCarsTable(data); })
      .catch(function (err) {
        renderCarsTable([]);
        showNotification(err.message, 'error');
      });
  }

  function loadMovementsTab() {
    API.fetchMovements()
      .then(function (data) { renderMovementsTable(data); })
      .catch(function (err) {
        renderMovementsTable([]);
        showNotification(err.message, 'error');
      });
  }

  function loadSalesTab() {
    API.fetchSales()
      .then(function (data) { renderSalesTable(data); })
      .catch(function (err) {
        renderSalesTable([]);
        showNotification(err.message, 'error');
      });
  }

  function initNavigation() {
    const nav = document.querySelector('#mainTabs [data-bs-toggle="tab"]');
    if (!nav) return;
    document.querySelectorAll('#mainTabs [data-bs-target]').forEach(function (tab) {
      tab.addEventListener('shown.bs.tab', function (e) {
        const target = e.target.getAttribute('data-bs-target');
        if (target === '#cars') loadCarsTab();
        else if (target === '#movements') loadMovementsTab();
        else if (target === '#sales') loadSalesTab();
      });
    });
  }

  function loadInitialData() {
    loadCarsTab();
    const filterStatus = document.getElementById('carsFilterStatus');
    if (filterStatus) {
      filterStatus.addEventListener('change', loadCarsTab);
    }
    const btnReportSales = document.getElementById('btnReportSales');
    const btnReportStock = document.getElementById('btnReportStock');
    const btnReportBuyers = document.getElementById('btnReportBuyers');
    const btnReportOperations = document.getElementById('btnReportOperations');
    if (btnReportSales) {
      btnReportSales.addEventListener('click', function () {
        API.fetchReportSales().then(function (data) { renderReport(data, 'sales'); }).catch(function (err) { showNotification(err.message, 'error'); });
      });
    }
    if (btnReportStock) {
      btnReportStock.addEventListener('click', function () {
        API.fetchReportStock().then(function (data) { renderReport(data, 'stock'); }).catch(function (err) { showNotification(err.message, 'error'); });
      });
    }
    if (btnReportBuyers) {
      btnReportBuyers.addEventListener('click', function () {
        API.fetchReportBuyers().then(function (data) { renderReport(data, 'buyers'); }).catch(function (err) { showNotification(err.message, 'error'); });
      });
    }
    if (btnReportOperations) {
      btnReportOperations.addEventListener('click', function () {
        API.fetchReportOperations().then(function (data) { renderReport(data, 'operations'); }).catch(function (err) { showNotification(err.message, 'error'); });
      });
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    const btnSelectFile = document.getElementById('btnSelectFile');
    const fileInput = document.getElementById('fileInput');
    if (btnSelectFile && fileInput) {
      btnSelectFile.addEventListener('click', function () {
        fileInput.click();
      });
    }
    bindCarsTableActions();
    initNavigation();
    loadInitialData();
  });
})();
