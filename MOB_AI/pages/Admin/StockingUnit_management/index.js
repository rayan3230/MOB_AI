import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  FlatList, 
  ActivityIndicator, 
  TouchableOpacity, 
  Alert, 
  Modal, 
  TextInput,
  ScrollView,
  Switch
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { productService } from '../../../services/productService';

const StockingUnitManagement = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
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

  const fetchData = async () => {
    try {
      setLoading(true);
      const data = await productService.getProducts();
      setProducts(data);
    } catch (error) {
      console.error('Error fetching products:', error);
      Alert.alert('Error', 'Failed to load products');
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
    fetchData();
  };

  const handleSubmitProduct = async () => {
    if (!newProduct.sku || !newProduct.nom_produit) {
      Alert.alert('Error', 'Please fill in SKU and Product Name');
      return;
    }

    try {
      setSubmitting(true);
      if (isEditing) {
        await productService.updateProduct(editingId, newProduct);
        Alert.alert('Success', 'Product updated successfully');
      } else {
        await productService.createProduct(newProduct);
        Alert.alert('Success', 'Product added successfully');
      }
      closeModal();
      fetchData();
    } catch (error) {
      console.error('Error submitting product:', error);
      Alert.alert('Error', `Failed to ${isEditing ? 'update' : 'add'} product`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteProduct = (id) => {
    Alert.alert(
      'Delete Product',
      'Are you sure you want to delete this product?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive',
          onPress: async () => {
            try {
              await productService.deleteProduct(id);
              Alert.alert('Success', 'Product deleted successfully');
              fetchData();
            } catch (error) {
              console.error('Error deleting product:', error);
              Alert.alert('Error', 'Failed to delete product');
            }
          }
        }
      ]
    );
  };

  const openEditModal = (prod) => {
    setNewProduct({
      sku: prod.sku,
      nom_produit: prod.nom_produit,
      unite_mesure: prod.unite_mesure,
      categorie: prod.categorie,
      collisage_palette: prod.collisage_palette ? prod.collisage_palette.toString() : '',
      collisage_fardeau: prod.collisage_fardeau ? prod.collisage_fardeau.toString() : '',
      poids: prod.poids ? prod.poids.toString() : '',
      actif: prod.actif
    });
    setEditingId(prod.id_produit);
    setIsEditing(true);
    setModalVisible(true);
  };

  const openAddModal = () => {
    setNewProduct({
      sku: '',
      nom_produit: '',
      unite_mesure: 'PCS',
      categorie: '',
      collisage_palette: '',
      collisage_fardeau: '',
      poids: '',
      actif: true
    });
    setIsEditing(false);
    setEditingId(null);
    setModalVisible(true);
  };

  const closeModal = () => {
    setModalVisible(false);
    setIsEditing(false);
  };

  const renderProductItem = ({ item }) => (
    <View style={styles.card}>
      <View style={styles.infoContainer}>
        <View style={styles.row}>
          <Text style={styles.skuText}>{item.sku}</Text>
          {!item.actif && (
            <View style={styles.inactiveBadge}>
              <Text style={styles.inactiveText}>INACTIVE</Text>
            </View>
          )}
        </View>
        <Text style={styles.nameText}>{item.nom_produit}</Text>
        <Text style={styles.subText}>
          {item.categorie} • {item.unite_mesure}
        </Text>
        <View style={styles.logisticsRow}>
          <View style={styles.logisticsItem}>
            <Feather name="box" size={12} color="#7f8c8d" />
            <Text style={styles.logisticsText}> P: {item.collisage_palette || 0}</Text>
          </View>
          <View style={styles.logisticsItem}>
            <Feather name="package" size={12} color="#7f8c8d" />
            <Text style={styles.logisticsText}> B: {item.collisage_fardeau || 0}</Text>
          </View>
          <View style={styles.logisticsItem}>
            <Feather name="database" size={12} color="#7f8c8d" />
            <Text style={styles.logisticsText}> {item.poids || 0}kg</Text>
          </View>
        </View>
      </View>
      
      <View style={styles.actionButtons}>
        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={() => openEditModal(item)}
        >
          <Feather name="edit-2" size={18} color="#2196F3" />
        </TouchableOpacity>
        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={() => handleDeleteProduct(item.id_produit)}
        >
          <Feather name="trash-2" size={18} color="#F44336" />
        </TouchableOpacity>
      </View>
    </View>
  );

  if (loading && !refreshing) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2196F3" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Produits / Unitées</Text>
        <TouchableOpacity 
          style={styles.addButton} 
          onPress={openAddModal}
        >
          <Text style={styles.addButtonText}>+ Ajouter Produit</Text>
        </TouchableOpacity>
      </View>
      
      {products.length === 0 ? (
        <View style={styles.centered}>
          <Text>Aucun produit trouvé</Text>
        </View>
      ) : (
        <FlatList
          data={products}
          keyExtractor={(item) => item.id_produit}
          renderItem={renderProductItem}
          onRefresh={onRefresh}
          refreshing={refreshing}
          contentContainerStyle={styles.listContainer}
        />
      )}

      <Modal
        animationType="slide"
        transparent={true}
        visible={modalVisible}
        onRequestClose={closeModal}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHandle} />
            <Text style={styles.modalTitle}>
              {isEditing ? 'Modifier Produit' : 'Ajouter Nouveau Produit'}
            </Text>
            
            <ScrollView style={styles.form}>
              <Text style={styles.label}>SKU *</Text>
              <TextInput
                style={styles.input}
                value={newProduct.sku}
                onChangeText={(t) => setNewProduct({...newProduct, sku: t})}
                placeholder="Unique SKU code"
              />

              <Text style={styles.label}>Nom Produit *</Text>
              <TextInput
                style={styles.input}
                value={newProduct.nom_produit}
                onChangeText={(t) => setNewProduct({...newProduct, nom_produit: t})}
                placeholder="Entrer nom produit"
              />

              <Text style={styles.label}>Catégorie</Text>
              <TextInput
                style={styles.input}
                value={newProduct.categorie}
                onChangeText={(t) => setNewProduct({...newProduct, categorie: t})}
                placeholder="e.g., Electronics, Food"
              />

              <Text style={styles.label}>Unitée de mesure</Text>
              <TextInput
                style={styles.input}
                value={newProduct.unite_mesure}
                onChangeText={(t) => setNewProduct({...newProduct, unite_mesure: t})}
                placeholder="e.g., PCS, KG, BOX"
              />

              <Text style={styles.label}>Poids (kg)</Text>
              <TextInput
                style={styles.input}
                value={newProduct.poids}
                onChangeText={(t) => setNewProduct({...newProduct, poids: t})}
                placeholder="0.00"
                keyboardType="numeric"
              />

              <Text style={styles.label}>Collisage Palette (qty par palette)</Text>
              <TextInput
                style={styles.input}
                value={newProduct.collisage_palette}
                onChangeText={(t) => setNewProduct({...newProduct, collisage_palette: t})}
                placeholder="0"
                keyboardType="numeric"
              />

              <Text style={styles.label}>Collisage Fardeau (qty par fardeau)</Text>
              <TextInput
                style={styles.input}
                value={newProduct.collisage_fardeau}
                onChangeText={(t) => setNewProduct({...newProduct, collisage_fardeau: t})}
                placeholder="0"
                keyboardType="numeric"
              />

              <View style={styles.switchRow}>
                <Text style={styles.label}>Actif</Text>
                <Switch
                  value={newProduct.actif}
                  onValueChange={(val) => setNewProduct({...newProduct, actif: val})}
                />
              </View>
            </ScrollView>

            <View style={styles.modalButtons}>
              <TouchableOpacity 
                style={[styles.modalButton, styles.cancelButton]} 
                onPress={closeModal}
                disabled={submitting}
              >
                <Text style={styles.cancelButtonText}>Annuler</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.modalButton, styles.saveButton]} 
                onPress={handleSubmitProduct}
                disabled={submitting}
              >
                {submitting ? (
                  <ActivityIndicator color="white" size="small" />
                ) : (
                  <Text style={styles.saveButtonText}>{isEditing ? 'Enregistrer' : 'Valider'}</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
    padding: 16,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
    marginTop: 8,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  addButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  addButtonText: {
    color: 'white',
    fontWeight: 'bold',
  },
  listContainer: {
    paddingBottom: 20,
  },
  card: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  infoContainer: {
    flex: 1,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  skuText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#3498db',
    marginRight: 8,
  },
  nameText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#2c3e50',
    marginBottom: 4,
  },
  subText: {
    fontSize: 14,
    color: '#7f8c8d',
  },
  logisticsRow: {
    flexDirection: 'row',
    marginTop: 8,
    gap: 12,
  },
  logisticsItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f1f3f5',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  logisticsText: {
    fontSize: 11,
    color: '#666',
    fontWeight: '500',
  },
  inactiveBadge: {
    backgroundColor: '#F44336',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  inactiveText: {
    color: 'white',
    fontSize: 10,
    fontWeight: 'bold',
  },
  actionButtons: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  actionButton: {
    padding: 8,
    marginLeft: 4,
    borderRadius: 8,
    backgroundColor: '#f1f3f5',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: 'white',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    maxHeight: '90%',
  },
  modalHandle: {
    width: 40,
    height: 5,
    backgroundColor: '#e0e0e0',
    borderRadius: 3,
    alignSelf: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
  },
  form: {
    marginBottom: 24,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    marginBottom: 6,
    marginTop: 12,
  },
  input: {
    backgroundColor: '#f8f9fa',
    borderWidth: 1,
    borderColor: '#e9ecef',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 16,
    paddingVertical: 8,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingBottom: 20,
  },
  modalButton: {
    flex: 1,
    padding: 14,
    borderRadius: 10,
    alignItems: 'center',
    marginHorizontal: 6,
  },
  saveButton: {
    backgroundColor: '#4CAF50',
  },
  cancelButton: {
    backgroundColor: '#f1f3f5',
  },
  saveButtonText: {
    color: 'white',
    fontWeight: 'bold',
  },
  cancelButtonText: {
    color: '#495057',
    fontWeight: 'bold',
  },
});

export default StockingUnitManagement;
