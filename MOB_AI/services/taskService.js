import { apiCall } from './api';

const mapTransactionToTask = (transaction) => ({
  id: transaction.id_transaction,
  title: transaction.reference_transaction || `Task ${transaction.id_transaction}`,
  description: transaction.notes || transaction.type_transaction || 'No details provided.',
  createdAt: transaction.cree_le,
  createdBy:
    transaction.cree_par_nom ||
    transaction?.cree_par_id_utilisateur?.user_name ||
    transaction?.cree_par_id_utilisateur?.username ||
    'Admin',
  status: transaction.statut,
  type: transaction.type_transaction,
});

export const taskService = {
  getTasks: async () => {
    const data = await apiCall('/api/transaction-management/', 'GET');
    if (!Array.isArray(data)) return [];
    return data.map(mapTransactionToTask);
  },

  markTaskDone: async (taskId) => {
    return await apiCall(`/api/transaction-management/${taskId}/complete_transaction/`, 'POST');
  },
};
