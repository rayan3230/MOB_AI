import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  FlatList, 
  ActivityIndicator, 
  TouchableOpacity, 
  Alert, 
  TextInput,
  Switch,
  StatusBar
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import OptionSelector from '../../../components/OptionSelector';
import { productService } from '../../../services/productService';
import { warehouseService } from '../../../services/warehouseService';
import CollapsibleManagementCard from '../../../components/CollapsibleManagementCard';
import ManagementModal from '../../../components/ManagementModal';
import { lightTheme } from '../../../constants/theme';

const PAGE_SIZE = 20;

const StockingUnitManagement = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [currentOffset, setCurrentOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [warehouses, setWarehouses] = useState([]);
  const [selectedWarehouseId, setSelectedWarehouseId] = useState('');
  const [warehouseFilterModalVisible, setWarehouseFilterModalVisible] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const [newProduct, setNewProduct] = useState({
    sku: '',
    nom_produit: '',
    unite_mesure: 'PCS',
    categorie: '',
    collisage_palette: '',
    collisage_fardeau: '',
    poids: '',
    actif: true
  });

  const fetchData = async (warehouseIdOverride = null) => {
    try {
      setLoading(true);
      const whData = await warehouseService.getWarehouses();
      setWarehouses(Array.isArray(whData) ? whData : []);

      const effectiveWhId = warehouseIdOverride !== null ? warehouseIdOverride : selectedWarehouseId;
      
      const response = await productService.getProductsPaged({
        warehouse_id: effectiveWhId || null,
        limit: PAGE_SIZE,
        offset: 0,
      });

      const results = response?.results || [];
      setProducts(results);
      setCurrentOffset(results.length);
      setHasMore(Boolean(response?.has_more));
    } catch (error) {
      console.error('Error fetching products:', error);
      Alert.alert('Erreur', 'Impossible de charger les produits');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchData(selectedWarehouseId);
  };

  const loadMore = async () => {
    if (loadingMore || !hasMore) return;
    try {
      setLoadingMore(true);
      const response = await productService.getProductsPaged({
        warehouse_id: selectedWarehouseId || null,
        limit: PAGE_SIZE,
        offset: currentOffset,
      });
      const next = response?.results || [];
      if (next.length > 0) {
        setProducts(prev => [...prev, ...next]);
        setCurrentOffset(prev => prev + next.length);
      }
      setHasMore(Boolean(response?.has_more));
    } catch (error) {
      console.error('Error loading more products:', error);
    } finally {
      setLoadingMore(false);
    }
  };

  const handleSubmit = async () => {
    if (!newProduct.sku || !newProduct.nom_produit) {
      Alert.alert('Erreur', 'SKU et Nom sont obligatoires');
      return;
    }
    try {
      setSubmitting(true);
      if (isEditing) {
        await productService.updateProduct(editingId, newProduct);
      } else {
        await productService.createProduct(newProduct);
      }
      setModalVisible(false);
      fetchData(selectedWarehouseId);
      Alert.alert('Succès', `Produit ${isEditing ? 'mis à jour' : 'ajouté'} avec succès`);
    } catch (error) {
      console.error('Submit error:', error);
      Alert.alert('Erreur', 'Échec de l\'opération');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = (id) => {
    Alert.alert('Supprimer Produit', 'Êtes-vous sûr ?', [
      { text: 'Annuler', style: 'cancel' },
      { text: 'Supprimer', style: 'destructive', onPress: async () => {
        try {
          await productService.deleteProduct(id);
          fetchData(selectedWarehouseId);
        } catch (error) {
          Alert.alert('Erreur', 'Échec de la suppression');
        }
      }}
    ]);
  };

  const openEdit = (prod) => {
    setNewProduct({
      sku: prod.sku,
      nom_produit: prod.nom_produit,
      unite_mesure: prod.unite_mesure,
      categorie: prod.categorie,
      collisage_palette: String(prod.collisage_palette || ''),
      collisage_fardeau: String(prod.collisage_fardeau || ''),
      poids: String(prod.poids || ''),
      actif: prod.actif
    });
    setEditingId(prod.id_produit);
    setIsEditing(true);
    setModalVisible(true);
  };

  const renderItem = ({ item }) => (
    <CollapsibleManagementCard
      title={item.sku}
      subtitle={item.nom_produit}
      status={item.actif ? 'ACTIF' : 'INACTIF'}
      iconName="package"
      iconColor={item.actif ? '#4CAF50' : '#8E8E93'}
      details={[
        { label: 'Catégorie', value: item.categorie || 'Général' },
        { label: 'Unité', value: item.unite_mesure },
        { label: 'Col. Palette', value: String(item.collisage_palette || 0) },
        { label: 'Col. Fardeau', value: String(item.collisage_fardeau || 0) },
        { label: 'Poids', value: item.poids ? `${item.poids} kg` : 'N/A' },
      ]}
      onEdit={() => openEdit(item)}
      onDelete={() => handleDelete(item.id_produit)}
    />
  );

  const selectedWarehouseLabel = selectedWarehouseId 
    ? warehouses.find(w => String(w.id_entrepot) === selectedWarehouseId)?.nom_entrepot 
    : 'Tous les entrepôts';

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Produits</Text>
          <Text style={styles.subtitle}>{selectedWarehouseLabel}</Text>
        </View>
        <View style={styles.headerActions}>
            <TouchableOpacity style={styles.filterButton} onPress={() => setWarehouseFilterModalVisible(true)}>
                <Feather name="filter" size={20} color="#2196F3" />
            </TouchableOpacity>
            <TouchableOpacity style={styles.addButton} onPress={() => {
                setNewProduct({ sku: '', nom_produit: '', unite_mesure: 'PCS', categorie: '', collisage_palette: '', collisage_fardeau: '', poids: '', actif: true });
                setIsEditing(false);
                setModalVisible(true);
            }}>
                <Feather name="plus" size={24} color="#FFF" />
            </TouchableOpacity>
        </View>
      </View>

      {loading && !refreshing ? (
        <View style={styles.centered}><ActivityIndicator size="large" color={lightTheme.primary} /></View>
      ) : (
        <FlatList
          data={products}
          keyExtractor={(item) => String(item.id_produit)}
          renderItem={renderItem}
          contentContainerStyle={styles.listContent}
          onRefresh={onRefresh}
          refreshing={refreshing}
          onEndReached={loadMore}
          onEndReachedThreshold={0.5}
          ListFooterComponent={loadingMore ? <ActivityIndicator size="small" color={lightTheme.primary} style={{ padding: 10 }} /> : null}
          ListEmptyComponent={
            <View style={styles.centered}>
                <Text style={styles.emptyText}>Aucun produit trouvé</Text>
            </View>
          }
        />
      )}

      {/* Filter Modal */}
      <ManagementModal
        visible={warehouseFilterModalVisible}
        onClose={() => setWarehouseFilterModalVisible(false)}
        title="Filtrer par Entrepôt"
        submitLabel="Appliquer"
        onSubmit={() => {
          setWarehouseFilterModalVisible(false);
          fetchData(selectedWarehouseId);
        }}
      >
        <OptionSelector
          label="Entrepôt"
          options={[
            { label: "Tous les entrepôts", value: "" },
            ...warehouses.map(w => ({ label: w.nom_entrepot, value: String(w.id_entrepot) }))
          ]}
          selectedValue={selectedWarehouseId}
          onValueChange={(val) => setSelectedWarehouseId(val)}
          icon="home"
        />
      </ManagementModal>

      {/* Add/Edit Modal */}
      <ManagementModal
        visible={modalVisible}
        onClose={() => setModalVisible(false)}
        title={isEditing ? 'Modifier Produit' : 'Nouveau Produit'}
        onSubmit={handleSubmit}
        submitting={submitting}
        submitLabel={isEditing ? 'Enregistrer' : 'Ajouter'}
      >
        <View style={styles.formGroup}>
          <Text style={styles.label}>SKU *</Text>
          <View style={styles.inputContainer}>
            <Feather name="hash" size={18} color="#94A3B8" style={styles.inputIcon} />
            <TextInput 
              style={styles.input} 
              placeholder="e.g., PRD-001" 
              value={newProduct.sku} 
              onChangeText={(t) => setNewProduct({...newProduct, sku: t})} 
              placeholderTextColor="#94A3B8"
            />
          </View>
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Nom du Produit *</Text>
          <View style={styles.inputContainer}>
            <Feather name="tag" size={18} color="#94A3B8" style={styles.inputIcon} />
            <TextInput 
              style={styles.input} 
              placeholder="Nom" 
              value={newProduct.nom_produit} 
              onChangeText={(t) => setNewProduct({...newProduct, nom_produit: t})} 
              placeholderTextColor="#94A3B8"
            />
          </View>
        </View>

        <View style={styles.row}>
            <View style={[styles.formGroup, {flex: 1, marginRight: 10}]}>
                <OptionSelector
                  label="Unité"
                  options={[
                    { label: "Pièces", value: "PCS" },
                    { label: "Kilogrammes", value: "KG" },
                    { label: "Litres", value: "L" },
                    { label: "Cartons", value: "BX" },
                  ]}
                  selectedValue={newProduct.unite_mesure}
                  onValueChange={(v) => setNewProduct({...newProduct, unite_mesure: v})}
                  icon="box"
                />
            </View>
            <View style={[styles.formGroup, {flex: 1}]}>
                <Text style={styles.label}>Catégorie</Text>
                <View style={styles.inputContainer}>
                    <Feather name="folder" size={18} color="#94A3B8" style={styles.inputIcon} />
                    <TextInput 
                      style={styles.input} 
                      placeholder="Catégorie" 
                      value={newProduct.categorie} 
                      onChangeText={(t) => setNewProduct({...newProduct, categorie: t})} 
                      placeholderTextColor="#94A3B8"
                    />
                </View>
            </View>
        </View>

        <View style={styles.row}>
            <View style={[styles.formGroup, {flex: 1, marginRight: 10}]}>
                <Text style={styles.label}>Col. Palette</Text>
                <View style={styles.inputContainer}>
                    <Feather name="layers" size={18} color="#94A3B8" style={styles.inputIcon} />
                    <TextInput 
                      style={styles.input} 
                      placeholder="Qté" 
                      keyboardType="numeric" 
                      value={newProduct.collisage_palette} 
                      onChangeText={(t) => setNewProduct({...newProduct, collisage_palette: t})} 
                      placeholderTextColor="#94A3B8"
                    />
                </View>
            </View>
            <View style={[styles.formGroup, {flex: 1}]}>
                <Text style={styles.label}>Col. Fardeau</Text>
                <View style={styles.inputContainer}>
                    <Feather name="package" size={18} color="#94A3B8" style={styles.inputIcon} />
                    <TextInput 
                      style={styles.input} 
                      placeholder="Qté" 
                      keyboardType="numeric" 
                      value={newProduct.collisage_fardeau} 
                      onChangeText={(t) => setNewProduct({...newProduct, collisage_fardeau: t})} 
                      placeholderTextColor="#94A3B8"
                    />
                </View>
            </View>
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Poids (kg)</Text>
          <View style={styles.inputContainer}>
            <Feather name="truck" size={18} color="#94A3B8" style={styles.inputIcon} />
            <TextInput 
              style={styles.input} 
              placeholder="Poids" 
              keyboardType="numeric" 
              value={newProduct.poids} 
              onChangeText={(t) => setNewProduct({...newProduct, poids: t})} 
              placeholderTextColor="#94A3B8"
            />
          </View>
        </View>

        <View style={styles.switchGroup}>
            <View style={styles.switchInfo}>
                <Text style={styles.label}>Statut Actif</Text>
                <Text style={styles.switchSubtitle}>Visible dans les opérations</Text>
            </View>
            <Switch
                value={newProduct.actif}
                onValueChange={(v) => setNewProduct({...newProduct, actif: v})}
                trackColor={{ false: '#D1D1D6', true: '#34C759' }}
                thumbColor="#FFF"
            />
        </View>
      </ManagementModal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: lightTheme.primary },
  header: {
    paddingHorizontal: 24,
    paddingBottom: 24,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerActions: { flexDirection: 'row', alignItems: 'center' },
  title: { fontSize: 28, fontWeight: '800', color: '#0F172A' },
  subtitle: { fontSize: 14, color: '#64748B', marginTop: 2 },
  addButton: {
    width: 48, height: 48, borderRadius: 14, backgroundColor: lightTheme.primary,
    justifyContent: 'center', alignItems: 'center', marginLeft: 12,
    elevation: 4, shadowColor: lightTheme.primary, shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3, shadowRadius: 8
  },
  filterButton: {
    width: 48, height: 48, borderRadius: 14, backgroundColor: '#F1F5F9',
    justifyContent: 'center', alignItems: 'center'
  },
  listContent: { paddingVertical: 12, paddingBottom: 100 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  label: { fontSize: 14, fontWeight: '700', marginBottom: 8, color: '#475569' },
  formGroup: { marginBottom: 20 },
  inputContainer: {
    backgroundColor: '#F8FAFC', borderRadius: 12, paddingHorizontal: 12,
    borderWidth: 1, borderColor: '#E2E8F0', flexDirection: 'row', alignItems: 'center',
    height: 54
  },
  inputIcon: { marginRight: 10 },
  pickerContainer: {
    backgroundColor: '#F8FAFC', borderRadius: 12, borderWidth: 1, borderColor: '#E2E8F0', 
    overflow: 'hidden', height: 54, justifyContent: 'center'
  },
  pickerWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
  },
  picker: {
    flex: 1,
    height: 54,
    marginLeft: -8, // Compensate for picker internal padding
  },
  input: { flex: 1, height: 54, fontSize: 16, color: '#1E293B' },
  row: { flexDirection: 'row', alignItems: 'center' },
  switchGroup: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    paddingVertical: 15,
    backgroundColor: '#F8FAFC',
    paddingHorizontal: 15,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0'
  },
  switchInfo: { flex: 1 },
  switchSubtitle: { fontSize: 12, color: '#94A3B8', marginTop: -4 },
  emptyText: { color: '#94A3B8', marginTop: 20, fontSize: 16 },
});

export default StockingUnitManagement;
