time = data(:,1);       % First column is timestamps
ref = data(:,2:5);      % Next 4 columns reference quaternion [w, x, y, z]
pose = data(:,6:9);     % Next 4 columns pose quaternion [w, x, y, z]
err = data(:,10:13);    % Next 4 columns error quaternion [w, x, y, z]
u = data(:,14:16);      % Last 3 columns actuator [thrust, steer, elevator]
ed = data(:,17);        % Energy Detect from radio - only updates on reception
rssi = data(:,18);      % Probably not useful
    
time = time - time(1);  % Subtract offset and scale
time = time/625E3;      % 625 ticks per millisecond

figure;
plot(time, ref(:,1), '-k.', time, ref(:,2), '-b.', time, ref(:,3), '-r.', time, ref(:,4), '-g.')
legend('w', 'x', 'y', 'z');
xlabel('Time, t (sec)')
ylabel('Quaternion components')
title('Reference vs. Time')

figure;
plot(time, pose(:,1), 'k.', time, pose(:,2), 'b.', time, pose(:,3), 'r.', time, pose(:,4), 'g.')
legend('w', 'x', 'y', 'z');
xlabel('Time, t (sec)')
ylabel('Quaternion components')
title('Pose vs. Time')

figure;
plot(time, err(:,1), 'k.', time, err(:,2), 'b.', time, err(:,3), 'r.', time, err(:,4), 'g.');
legend('Angle', 'Roll', 'Pitch', 'Yaw');
xlabel('Time, t (sec)')
ylabel('Quaternion component');
title('Raw Error vs. Time')

figure;
plot(time, err(:,3), 'b.', time, u(:,3), '-r.', time, u(:,1), '-g.')
legend('Pitch Error', 'Elevator Output', 'Thrust')
xlabel('Time, t (sec)');
title('Pitch Control Trace')

figure;
plot(time, err(:,4), 'b.', time, u(:,2), '-r.')
legend('Yaw Error', 'Steer Output')
xlabel('Time, t (sec)');
title('Yaw Control Trace')