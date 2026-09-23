/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";
import { Component, onWillStart, useState, useRef, onMounted, onPatched } from "@odoo/owl";

const CHART_COLORS = {
    deepBlue: "#0B5FA3",
    success: "#1E8E5A",
    warning: "#C77700",
    danger: "#C22B2B",
};

export class SeyalDashboard extends Component {
    static template = "seyal_dashboard.DashboardTemplate";

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            kpis: null,
            dailySeries: [],
            dailyDays: 30,
            loading: true,
        });

        this.dailyCanvas = useRef("dailyChart");
        this._charts = {};
        this._chartsDirty = false;

        this.dailyDaysOptions = [7, 30, 90];

        this.sections = [
            {
                title: "Ventes & Achats",
                tiles: [
                    { key: "ca_today", label: "CA du jour", icon: "fa-calendar", tone: "primary" },
                    { key: "ca_month", label: "CA du mois", icon: "fa-line-chart", tone: "primary" },
                    { key: "ventes_count", label: "Commandes du mois", icon: "fa-shopping-cart", tone: "info", isCount: true },
                    { key: "ventes_amount", label: "Ventes du mois", icon: "fa-money", tone: "success" },
                    { key: "achats_amount", label: "Achats du mois", icon: "fa-truck", tone: "warning" },
                ],
            },
            {
                title: "Finance",
                tiles: [
                    { key: "marge_month", label: "Marge du mois", icon: "fa-balance-scale", tone: "success" },
                    { key: "benefice_month", label: "Benefice du mois", icon: "fa-trophy", tone: "success" },
                    { key: "encaissements_month", label: "Encaissements du mois", icon: "fa-arrow-down", tone: "success" },
                    { key: "depenses_month", label: "Depenses du mois", icon: "fa-arrow-up", tone: "danger" },
                    { key: "creances_total", label: "Creances clients", icon: "fa-hand-o-right", tone: "info" },
                    { key: "dettes_total", label: "Dettes fournisseurs", icon: "fa-hand-o-left", tone: "danger" },
                ],
            },
            {
                title: "Stock & Logistique",
                tiles: [
                    { key: "stock_value", label: "Valeur du stock", icon: "fa-cubes", tone: "primary" },
                    { key: "ruptures_count", label: "Ruptures de stock", icon: "fa-exclamation-triangle", tone: "danger", isCount: true },
                    { key: "importations_en_cours", label: "Importations en cours", icon: "fa-ship", tone: "info", isCount: true },
                    { key: "livraisons_en_cours", label: "Livraisons en cours", icon: "fa-truck", tone: "info", isCount: true },
                ],
            },
        ];

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
            await this.loadAll();
        });

        onMounted(() => {
            this._drawCharts();
        });
        onPatched(() => {
            if (this._chartsDirty) {
                this._drawCharts();
                this._chartsDirty = false;
            }
        });
    }

    async loadAll() {
        this.state.loading = true;
        const [kpis, dailySeries] = await Promise.all([
            this.orm.call("seyal.dashboard", "get_kpis", []),
            this.orm.call("seyal.dashboard", "get_daily_series", [], { days: this.state.dailyDays }),
        ]);
        this.state.kpis = kpis;
        this.state.dailySeries = dailySeries;
        this.state.loading = false;
        this._chartsDirty = true;
    }

    async onDailyDaysChange(days) {
        this.state.dailyDays = days;
        this.state.dailySeries = await this.orm.call("seyal.dashboard", "get_daily_series", [], { days });
        this._chartsDirty = true;
        this.render();
    }

    _destroyChart(key) {
        if (this._charts[key]) {
            this._charts[key].destroy();
            delete this._charts[key];
        }
    }

    _drawCharts() {
        if (!window.Chart) {
            return;
        }
        this._drawDailyChart();
    }

    _drawDailyChart() {
        const canvas = this.dailyCanvas.el;
        if (!canvas) return;
        this._destroyChart("daily");
        const labels = this.state.dailySeries.map((d) => d.date.slice(5));
        this._charts.daily = new window.Chart(canvas, {
            type: "bar",
            data: {
                labels,
                datasets: [
                    {
                        type: "line", label: "CA facture", data: this.state.dailySeries.map((d) => d.ca),
                        borderColor: CHART_COLORS.deepBlue, backgroundColor: CHART_COLORS.deepBlue,
                        tension: 0.25, yAxisID: "y",
                    },
                    {
                        type: "bar", label: "Encaisse", data: this.state.dailySeries.map((d) => d.encaisse),
                        backgroundColor: CHART_COLORS.success, yAxisID: "y",
                    },
                ],
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: "index", intersect: false },
                plugins: { legend: { position: "bottom" } },
                scales: { y: { beginAtZero: true } },
            },
        });
    }

    formatValue(value) {
        if (typeof value !== "number") {
            return value;
        }
        return value.toLocaleString("fr-FR", { maximumFractionDigits: 2 });
    }
}

registry.category("actions").add("seyal_dashboard", SeyalDashboard);
