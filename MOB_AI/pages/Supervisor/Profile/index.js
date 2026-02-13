import React from 'react';
import ProfileContent from '../../common/ProfileContent';

const SupervisorProfile = ({ navigation, user, onOpenDrawer }) => {
  return <ProfileContent role="supervisor" user={user} navigation={navigation} onOpenDrawer={onOpenDrawer} />;
};

export default SupervisorProfile;
