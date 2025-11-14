import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

function ChartsSection({ categoryChartData, statusData, consumptionData, colors }) {
    return (
        <div className="charts-section">
            <div className="chart-card">
                <h3 className="chart-title">Inventory Distribution by Category</h3>
                <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={categoryChartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                        <XAxis dataKey="name" stroke={colors.textSecondary} />
                        <YAxis stroke={colors.textSecondary} />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: colors.bg,
                                border: `1px solid ${colors.border}`,
                                borderRadius: '8px',
                                color: colors.text
                            }}
                        />
                        <Legend wrapperStyle={{ color: colors.textSecondary }} />
                        <Bar dataKey="quantity" fill="#667eea" radius={[8, 8, 0, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </div>

            <div className="chart-card">
                <h3 className="chart-title">Stock Status Overview</h3>
                <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                        <Pie
                            data={statusData}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                            outerRadius={100}
                            fill="#8884d8"
                            dataKey="value"
                        >
                            {statusData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                        </Pie>
                        <Tooltip
                            contentStyle={{
                                backgroundColor: colors.bg,
                                border: `1px solid ${colors.border}`,
                                borderRadius: '8px',
                                color: colors.text
                            }}
                        />
                    </PieChart>
                </ResponsiveContainer>
            </div>

            <div className="chart-card full-width">
                <h3 className="chart-title">Consumption Rate (Last 6 Months)</h3>
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={consumptionData}>
                        <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                        <XAxis dataKey="month" stroke={colors.textSecondary} />
                        <YAxis stroke={colors.textSecondary} />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: colors.bg,
                                border: `1px solid ${colors.border}`,
                                borderRadius: '8px',
                                color: colors.text
                            }}
                        />
                        <Legend wrapperStyle={{ color: colors.textSecondary }} />
                        <Line
                            type="monotone"
                            dataKey="usage"
                            stroke="#4facfe"
                            strokeWidth={3}
                            dot={{ fill: '#4facfe', r: 6 }}
                            activeDot={{ r: 8 }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    )
}

export default ChartsSection
