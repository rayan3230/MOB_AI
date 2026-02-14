import React, { useEffect, useState, useRef } from 'react';
import { View, StyleSheet, ActivityIndicator, Text, Dimensions, ScrollView, TouchableOpacity } from 'react-native';
import Svg, { Rect, Path, G, Circle, Text as SvgText } from 'react-native-svg';
import { Feather } from '@expo/vector-icons';
import { aiService } from '../services/aiService';

const WarehouseMap = ({ floorIdx = 0, routeData = null, zoningData = null, mode = 'route' }) => {
    const [mapData, setMapData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [zoom, setZoom] = useState(1);

    const screenWidth = Dimensions.get('window').width - 40;
    const [baseScale, setBaseScale] = useState(10);

    const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.5, 4));
    const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.5, 0.5));
    const handleReset = () => setZoom(1);

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
                setBaseScale(s);
            } else {
                setError('Failed to load map layout');
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <View style={styles.loader}><ActivityIndicator size="large" color="#0000ff" /></View>;
    if (error) return <Text style={styles.error}>{error}</Text>;
    if (!mapData) return null;

    const { width, height, zones, landmarks } = mapData;
    const currentScale = baseScale * zoom;

    return (
        <View style={styles.outerContainer}>
            {/* Zoom Controls Overlay */}
            <View style={styles.zoomControls}>
                <TouchableOpacity style={styles.zoomButton} onPress={handleZoomIn}>
                    <Feather name="plus" size={22} color="#007AFF" />
                </TouchableOpacity>
                <TouchableOpacity style={styles.zoomButton} onPress={handleZoomOut}>
                    <Feather name="minus" size={22} color="#007AFF" />
                </TouchableOpacity>
                <TouchableOpacity style={styles.zoomButton} onPress={handleReset}>
                    <Feather name="refresh-cw" size={18} color="#666" />
                </TouchableOpacity>
            </View>

            {/* Hint Overlay */}
            <View style={styles.hintOverlay}>
                <Text style={styles.hintText}>{(zoom * 100).toFixed(0)}% | Pan to explore</Text>
            </View>

            <ScrollView 
                style={styles.scrollView}
                contentContainerStyle={styles.verticalScrollContent}
                nestedScrollEnabled={true}
            >
                <ScrollView 
                    horizontal 
                    nestedScrollEnabled={true}
                    contentContainerStyle={styles.horizontalScrollContent}
                >
                    <View style={[
                        styles.mapWrapper, 
                        { 
                            width: Math.max(width * currentScale, screenWidth), 
                            height: Math.max(height * currentScale, 300) 
                        }
                    ]}>
                        <Svg width={width * currentScale} height={height * currentScale} viewBox={`0 0 ${width} ${height}`}>
                            {/* Background */}
                            <Rect x="0" y="0" width={width} height={height} fill="#f0f0f0" stroke="#ccc" strokeWidth="0.1" />

                            {/* Zones/Racks */}
                            {Object.entries(zones).map(([name, coords]) => {
                                // Handle both single rect [x1, y1, x2, y2] and multiple rects [[x1, y1, x2, y2], ...]
                                const rects = Array.isArray(coords[0]) ? coords : [coords];
                                
                                let fill = '#dcdde1';
                                let stroke = '#7f8c8d';

                                if (name.includes('Expédition')) {
                                    fill = '#fbc531';
                                    stroke = '#e1b12c';
                                } else if (name === 'Bureau' || name.includes('Assenseur') || name.includes('Charge')) {
                                    fill = '#9c88ff';
                                    stroke = '#8c7ae6';
                                } else if (name.match(/^[A-Z][0-9]+/)) { // Racks A1, B2, etc.
                                    fill = '#4b7bef';
                                    stroke = '#2f3640';
                                }

                                return (
                                    <G key={name}>
                                        {rects.map((rect, rIdx) => {
                                            const [x1, y1, x2, y2] = rect;
                                            return (
                                                <Rect
                                                    key={`${name}-rect-${rIdx}`}
                                                    x={x1}
                                                    y={height - y2} // Flipped Y
                                                    width={x2 - x1}
                                                    height={y2 - y1}
                                                    fill={fill}
                                                    stroke={stroke}
                                                    strokeWidth="0.1"
                                                    opacity="0.6"
                                                />
                                            );
                                        })}
                                        {/* Label at the center of the first rectangle */}
                                        <SvgText
                                            x={(rects[0][0] + rects[0][2]) / 2}
                                            y={height - (rects[0][1] + rects[0][3]) / 2} // Flipped Y
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

                {/* Landmarks (POI) */}
                {landmarks && Object.entries(landmarks).map(([name, coord]) => (
                    <G key={`landmark-${name}`}>
                        <Circle cx={coord.x} cy={height - coord.y} r="0.3" fill="#e74c3c" />
                        <SvgText
                            x={coord.x}
                            y={height - coord.y - 0.5} // Flipped Y + offset
                            fontSize="0.5"
                            fill="#c0392b"
                            textAnchor="middle"
                            fontWeight="600"
                        >
                            {name}
                        </SvgText>
                    </G>
                ))}

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
                            cx={x + 0.5} // Offset centered
                            cy={height - (y + 0.5)} // Flipped Y + centered
                            r="0.4" 
                            fill={color} 
                            opacity="0.5" 
                        />
                    );
                })}

                {/* Optimized Route */}
                {routeData && routeData.path_segments && routeData.path_segments.map((segment, idx) => {
                    const pathD = segment.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p[0]} ${height - p[1]}`).join(' ');
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
                        <Circle cx={p[0]} cy={height - p[1]} r="0.4" fill="#e84118" />
                        <SvgText
                            x={p[0]}
                            y={height - p[1] - 0.6} // Flipped Y + offset
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
    </ScrollView>
</ScrollView>
</View>
);
};

const styles = StyleSheet.create({
    outerContainer: {
        flex: 1,
        width: '100%',
        height: 400,
        backgroundColor: '#f8f9fa',
        borderRadius: 12,
        overflow: 'hidden',
        borderWidth: 1,
        borderColor: '#e9ecef',
    },
    scrollView: {
        flex: 1,
    },
    verticalScrollContent: {
        flexGrow: 1,
    },
    horizontalScrollContent: {
        flexGrow: 1,
    },
    mapWrapper: {
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f0f0f0',
    },
    zoomControls: {
        position: 'absolute',
        right: 12,
        bottom: 12,
        zIndex: 10,
        gap: 8,
    },
    zoomButton: {
        width: 44,
        height: 44,
        backgroundColor: '#ffffff',
        borderRadius: 22,
        justifyContent: 'center',
        alignItems: 'center',
        elevation: 6,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 3 },
        shadowOpacity: 0.25,
        shadowRadius: 4.65,
        borderWidth: 1,
        borderColor: '#dee2e6',
    },
    hintOverlay: {
        position: 'absolute',
        left: 12,
        top: 12,
        zIndex: 10,
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 12,
    },
    hintText: {
        color: '#fff',
        fontSize: 10,
        fontWeight: 'bold',
    },
    loader: {
        height: 400,
        justifyContent: 'center',
        alignItems: 'center',
        width: '100%',
    },
    error: {
        color: 'red',
        textAlign: 'center',
        margin: 10,
    }
});

export default WarehouseMap;
