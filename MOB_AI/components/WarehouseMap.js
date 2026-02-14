import React, { useEffect, useState } from 'react';
import { View, StyleSheet, ActivityIndicator, Text, Dimensions } from 'react-native';
import Svg, { Rect, Path, G, Circle, Text as SvgText } from 'react-native-svg';
import { aiService } from '../services/aiService';

const WarehouseMap = ({ floorIdx = 0, routeData = null, zoningData = null, mode = 'route' }) => {
    const [mapData, setMapData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const screenWidth = Dimensions.get('window').width - 40;
    const [scale, setScale] = useState(10);

    useEffect(() => {
        fetchMap();
    }, [floorIdx]);

    const fetchMap = async () => {
        try {
            setLoading(true);
            const data = await aiService.getDigitalTwinMap(floorIdx);
            if (data.status === 'success') {
                setMapData(data);
                // Calculate scale based on warehouse width and screen width
                const s = screenWidth / data.width;
                setScale(s);
            } else {
                setError('Failed to load map layout');
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <ActivityIndicator size="large" color="#0000ff" />;
    if (error) return <Text style={styles.error}>{error}</Text>;
    if (!mapData) return null;

    const { width, height, zones, landmarks } = mapData;

    return (
        <View style={styles.container}>
            <Svg width={width * scale} height={height * scale} viewBox={`0 0 ${width} ${height}`}>
                {/* Background */}
                <Rect x="0" y="0" width={width} height={height} fill="#f0f0f0" stroke="#ccc" strokeWidth="0.1" />

                {/* Zones/Racks */}
                {Object.entries(zones).map(([name, coords]) => {
                    // coords is [x1, y1, x2, y2]
                    const [x1, y1, x2, y2] = coords;
                    let fill = '#dcdde1';
                    let stroke = '#7f8c8d';

                    if (name.includes('Expédition')) {
                        fill = '#fbc531';
                        stroke = '#e1b12c';
                    } else if (name === 'Bureau') {
                        fill = '#9c88ff';
                        stroke = '#8c7ae6';
                    } else if (name.includes('Rack')) {
                        fill = '#4b7bef';
                        stroke = '#2f3640';
                    }

                    return (
                        <G key={name}>
                            <Rect
                                x={x1}
                                y={y1}
                                width={x2 - x1}
                                height={y2 - y1}
                                fill={fill}
                                stroke={stroke}
                                strokeWidth="0.1"
                                opacity="0.6"
                            />
                            <SvgText
                                x={(x1 + x2) / 2}
                                y={(y1 + y2) / 2}
                                fontSize="0.8"
                                fill={stroke}
                                textAnchor="middle"
                                alignmentBaseline="middle"
                                fontWeight="bold"
                            >
                                {name}
                            </SvgText>
                        </G>
                    );
                })}

                {/* AI Zoning Heatmap (Requirement 8.2) */}
                {mode === 'zoning' && zoningData && Object.entries(zoningData.zoning).map(([coordStr, storageClass]) => {
                    const [x, y] = coordStr.split(',').map(Number);
                    let color = '#7f8c8d'; // Default
                    if (storageClass === 'FAST') color = '#27ae60'; // Green
                    if (storageClass === 'MEDIUM') color = '#f1c40f'; // Yellow
                    if (storageClass === 'SLOW') color = '#e74c3c'; // Red
                    
                    return (
                        <Circle 
                            key={`zone-${coordStr}`}
                            cx={x} 
                            cy={y} 
                            r="0.4" 
                            fill={color} 
                            opacity="0.5" 
                        />
                    );
                })}

                {/* Optimized Route */}
                {routeData && routeData.path_segments && routeData.path_segments.map((segment, idx) => {
                    const pathD = segment.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p[0]} ${p[1]}`).join(' ');
                    return (
                        <Path
                            key={`route-${idx}`}
                            d={pathD}
                            stroke="#e84118"
                            strokeWidth="0.3"
                            fill="none"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeDasharray="0.5, 0.5"
                        />
                    );
                })}

                {/* Target Points (Picks) */}
                {routeData && routeData.route_sequence && routeData.route_sequence.map((p, idx) => (
                    <G key={`pick-${idx}`}>
                        <Circle cx={p[0]} cy={p[1]} r="0.4" fill="#e84118" />
                        <SvgText
                            x={p[0]}
                            y={p[1] - 0.6}
                            fontSize="0.6"
                            fill="#000"
                            textAnchor="middle"
                            fontWeight="bold"
                        >
                            {idx + 1}
                        </SvgText>
                    </G>
                ))}
            </Svg>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        alignItems: 'center',
        justifyContent: 'center',
        marginVertical: 10,
        backgroundColor: '#fff',
        padding: 10,
        borderRadius: 12,
        elevation: 3,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
    },
    error: {
        color: 'red',
        textAlign: 'center',
        margin: 10,
    }
});

export default WarehouseMap;
