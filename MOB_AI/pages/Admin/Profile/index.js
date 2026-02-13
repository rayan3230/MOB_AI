import React from 'react';
import ProfileContent from '../../common/ProfileContent';

const AdminProfile = ({ navigation, user, onOpenDrawer }) => {
  return <ProfileContent role="admin" user={user} navigation={navigation} onOpenDrawer={onOpenDrawer} />;
};

export default AdminProfile;
