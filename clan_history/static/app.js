var clanHistoryApp = angular.module('clanHistoryApp', []);

clanHistoryApp.controller('PlayerCtrl', function ($scope, $http) {
  $scope.search = function() {
    $http.get('player/' + $scope.player_name).success(function(data) {
      data.history.map(function(h) {
        h.created_at = moment(h.created_at * 1000).zone('+0200').format('DD.MM.YYYY HH:mm');
        h.last_seen = moment(h.last_seen * 1000).zone('+0200').format('DD.MM.YYYY HH:mm');
        var clan_id_str = h.clan_id.toString().substring(h.clan_id.toString().length - 3, h.clan_id.toString().length);
        h.emblem_url = 'http://clans.worldoftanks.eu/media/clans/emblems/cl_' + clan_id_str + '/' + h.clan_id + '/emblem_32x32.png';
      });


      $scope.player = data;

    });
  };
});
