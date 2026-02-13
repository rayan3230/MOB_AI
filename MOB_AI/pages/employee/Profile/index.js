import React from 'react';
import ProfileContent from '../../common/ProfileContent';

const EmployeeProfile = ({ route, navigation }) => {
  const { user } = route.params || {};
  return <ProfileContent role="employee" user={user} navigation={navigation} />;
};

export default EmployeeProfile;
