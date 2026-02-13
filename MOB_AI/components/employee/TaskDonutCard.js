import React, { useMemo } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Circle } from 'react-native-svg';
import { lightTheme } from '../../constants/theme';

const size = 190;
const strokeWidth = 28;
const radius = (size - strokeWidth) / 2;
const circumference = 2 * Math.PI * radius;

const segmentsMeta = [
  { key: 'pending', label: 'Pending', color: lightTheme.primary },
  { key: 'confirmed', label: 'Confirmed', color: lightTheme.secondary },
  { key: 'completed', label: 'Completed', color: lightTheme.thirdary },
];

const TaskDonutCard = ({ stats }) => {
  const { total, segments } = useMemo(() => {
    const values = {
      pending: stats?.pending || 0,
      confirmed: stats?.confirmed || 0,
      completed: stats?.completed || 0,
    };

    const overall = values.pending + values.confirmed + values.completed;
    const fallbackTotal = overall || 1;

    let offsetCursor = 0;
    const computedSegments = segmentsMeta.map((segment) => {
      const rawValue = values[segment.key];
      const ratio = rawValue / fallbackTotal;
      const strokeDasharray = `${Math.max(ratio * circumference, 0)} ${circumference}`;
      const strokeDashoffset = -offsetCursor;
      offsetCursor += ratio * circumference;

      return {
        ...segment,
        value: rawValue,
        strokeDasharray,
        strokeDashoffset,
      };
    });

    return {
      total: overall,
      segments: computedSegments,
    };
  }, [stats]);

  return (
    <View style={styles.card}>
      <Text style={styles.title}>Task analytics</Text>
      <View style={styles.contentRow}>
        <View style={styles.chartWrap}>
          <Svg width={size} height={size}>
            <Circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              stroke={lightTheme.divider}
              strokeWidth={strokeWidth}
              fill="none"
            />
            {segments.map((segment) => (
              <Circle
                key={segment.key}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                stroke={segment.color}
                strokeWidth={strokeWidth}
                fill="none"
                strokeDasharray={segment.strokeDasharray}
                strokeDashoffset={segment.strokeDashoffset}
                strokeLinecap="butt"
                transform={`rotate(-90 ${size / 2} ${size / 2})`}
              />
            ))}
          </Svg>
          <View style={styles.centerLabel}>
            <Text style={styles.totalValue}>{total}</Text>
            <Text style={styles.totalText}>Total tasks</Text>
          </View>
        </View>

        <View style={styles.legendWrap}>
          {segments.map((segment) => (
            <View key={segment.key} style={styles.legendRow}>
              <View style={[styles.legendDot, { backgroundColor: segment.color }]} />
              <View>
                <Text style={styles.legendTitle}>{segment.label}</Text>
                <Text style={styles.legendValue}>{segment.value}</Text>
              </View>
            </View>
          ))}
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    borderRadius: 16,
    borderWidth: 1,
    borderColor: lightTheme.border,
    backgroundColor: lightTheme.white,
    padding: 14,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: lightTheme.textPrimary,
    marginBottom: 8,
  },
  contentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  chartWrap: {
    width: 210,
    height: 210,
    alignItems: 'center',
    justifyContent: 'center',
  },
  centerLabel: {
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
  },
  totalValue: {
    fontSize: 32,
    fontWeight: '700',
    color: lightTheme.textPrimary,
  },
  totalText: {
    fontSize: 13,
    color: lightTheme.textSecondary,
    fontWeight: '500',
  },
  legendWrap: {
    flex: 1,
    paddingLeft: 8,
    gap: 12,
  },
  legendRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  legendDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  legendTitle: {
    color: lightTheme.textSecondary,
    fontSize: 12,
    fontWeight: '500',
  },
  legendValue: {
    color: lightTheme.textPrimary,
    fontSize: 15,
    fontWeight: '700',
  },
});

export default TaskDonutCard;
