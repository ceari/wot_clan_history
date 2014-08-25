var clanHistoryApp = angular.module('clanHistoryApp', []);

clanHistoryApp.controller('PlayerCtrl', function ($scope, $http) {
  $scope.search = function() {
    $http.get('player/' + $scope.player_name).success(function(data) {
      $scope.player = data;
    });
  };
});
